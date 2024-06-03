import os
import requests
from dataclasses import dataclass

SUINFRA_TEST_ID = "1c4ffcd5-c7b7-44f6-9769-23e6d5e23799"

FLY_REGIONS = [
    "ams",
    "arn",
    "atl",
    "bog",
    "bom",
    "bos",
    "cdg",
    "den",
    "dfw",
    "eze",
    "ewr",
    "fra",
    "gdl",
    "gig",
    "gru",
    "hkg",
    "iad",
    "jnb",
    "lax",
    "lhr",
    "mad",
    "mia",
    "nrt",
    "ord",
    "otp",
    "phx",
    "qro",
    "scl",
    "sea",
    "sin",
    "sjc",
    "syd",
    "waw",
    "yul",
    "yyz",
]


@dataclass
class RpcEndpoint:
    name: str
    url: str


def get_rpc_order_for_regions():
    r = requests.get(f"https://suinfra.io/api/v1/rpc/{SUINFRA_TEST_ID}/")
    data = r.json()["data"]

    regional_rpcs = {}

    for region, rpcs in data.items():
        rpcs_for_region = []
        for rpc in rpcs:
            # Skip paid endpoints.
            if rpc["rpc_name"].endswith("_paid"):
                continue
            # Skip TritonOne.
            if rpc["rpc_name"].startswith("triton_one"):
                continue
            print(rpc["rpc_name"], rpc["avg_latency"])
            rpc_endpoint = RpcEndpoint(
                name=rpc["rpc_name"].replace("_free", ""),
                url=rpc["rpc_url"],
            )
            rpcs_for_region.append(rpc_endpoint)
        regional_rpcs[region] = rpcs_for_region

    return regional_rpcs


def generate_rpc_pool_backend_config(
    rpcs: list[RpcEndpoint],
):
    servers: list[str] = []
    starting_port = 9000
    for index, rpc in enumerate(rpcs):
        server_line = f"\tserver {rpc.name}_backend 127.0.0.1:{starting_port + index} check maxconn 50"  # fmt: skip
        if index > 2:
            server_line = f"{server_line} backup"
        servers.append(server_line)

    config_text = (
        "backend rpc_pool_backend",
        "\toption httpchk",
        "\tbalance first",
        "\tdefault-server inter 30s fall 5 rise 3",
        """\thttp-check send meth POST uri / ver HTTP/1.1 hdr Content-Type application/json body '{"jsonrpc": "2.0", "method": "suix_getReferenceGasPrice", "params": [], "id":1}'""",
        "\thttp-check expect status 200",
        "\n".join(servers),
    )

    return "\n".join(config_text)


def generate_rpc_backend_configs(
    rpcs: list[RpcEndpoint],
):
    backends: list[str] = []
    for rpc in rpcs:
        config_text = (
            f"backend {rpc.name}_backend",
            "\tdefault-server inter 30s fall 5 rise 3",
            "\thttp-request set-header Content-Type application/json",
            f"\thttp-request set-header Host {rpc.url.replace('https://', '')}",
            '\thttp-response set-header X-Routed-By "$FLY_REGION":"$FLY_MACHINE_ID"',
            "\thttp-response set-header X-Routed-To %s",
            "\thttp-response set-header X-Edge-Region %s",
            f"\tserver {rpc.url.replace('https://', '')} {rpc.url.replace('https://', '')}:443 check ssl verify none check-sni {rpc.url.replace('https://', '')}",
        )
        backends.append("\n".join(config_text))

    return "\n\n".join(backends)


def generate_rpc_proxy_configs(
    rpcs: list[RpcEndpoint],
):
    proxies: list[str] = []
    starting_port = 9000
    for index, rpc in enumerate(rpcs):
        proxies.append(
            "\n".join(
                (
                    f"frontend {rpc.name}_proxy",
                    f"\tbind *:{starting_port + index}",
                    "\toption http-keep-alive",
                    f"\tdefault_backend {rpc.name}_backend",
                )
            )
        )

    return "\n\n".join(proxies)


def main():
    os.makedirs("./region_configs", exist_ok=True)

    regional_rpcs = get_rpc_order_for_regions()

    for region_code in FLY_REGIONS:
        print(f"Generating config for {region_code}...")
        rpcs = regional_rpcs[region_code]
        proxies = generate_rpc_proxy_configs(rpcs)
        pool_backend = generate_rpc_pool_backend_config(rpcs)
        rpc_backends = generate_rpc_backend_configs(rpcs)

        with open("./haproxy.cfg", "r+") as f:
            data = f.read()
            data = data.replace(
                "<DYNAMIC_CONFIG>",
                "\n\n".join(
                    (
                        proxies,
                        pool_backend,
                        rpc_backends,
                    )
                ),
            )

        with open(f"./region_configs/haproxy_{region_code}.cfg", "w+") as f:
            f.write(f"{data}\n")

    print("Done!")


if __name__ == "__main__":
    main()
