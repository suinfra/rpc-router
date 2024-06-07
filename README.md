# Suinfra RPC Router

The Suinfra RPC Router is a globally distributed and geographically-aware proxy that routes RPC requests to the closest RPC endpoint. We conceptualized and developed this project to support Sui's [Mysticeti consensus design](https://blog.sui.io/mysticeti-consensus-reduce-latency/), which is capable of achieving a time-to-finality (TTF) of 250ms for fast-path transactions and 500ms for consensus-path transactions.

Suinfra routinely conducts [RPC benchmark tests](https://suinfra.io/rpc/2d730281-e288-4c82-8abb-33e1a75968c5/) in 35 regions around the world. These benchmark results are also [available in JSON format](https://suinfra.io/api/v1/rpc/2d730281-e288-4c82-8abb-33e1a75968c5/) through the Suinfra API. As you can see in the benchmark results above, RPC latency can range from ~20ms to ~500ms depending on the user's region and chosen RPC endpoint. For blockchains with slower TTF (Ethereum, Avalanche, Polygon, etc.), an RPC response time of 500ms can't be "felt" as easily. In Sui's case, ~500ms is 2x is longer than the TTF of a fast-path transaction post-Mysticeti. Thus, maximizing the UX potential of Sui requires access to low-latency RPC endpoints.

## How it Works

With Suinfra benchmark results, we're able to objectively determine the fastest RPC endpoints in each region, and dynamically generate region-specific HAProxy configurations.

A base HAProxy configuration file can be found in `haproxy.cfg`. Within the base configuration file, there's a `<DYNAMIC_CONFIG>`variable that's replaced with region-specific backend information when running the `generate_region_configs.py` script. The `generate_region_configs.py` script fetches RPC results for the specified `SUINFRA_TEST_ID`, and dynamically generates HAProxy configuration files for each region, and stores them in `./region_configs`.

The proxy itself is designed to be deployed on [https://fly.io](Fly.io), an infrastructure provider that leverages [Anycast](https://fly.io/docs/networking/services/#anycast-ip-addresses) to route user requests to the closest Fly region. With this configuration, an RPC request from a user in Singapore will be routed to an HAProxy instance in Singapore, and then forwarded to the best-performing RPC endpoint from Singapore (based on Suinfra test results). Ultimately, this means users will be able to rely on a single RPC endpoint, no matter where they are in the world.

## How to Use the Suinfra RPC Endpoint

The Suinfra team operates a publicly-available endpoint that routes to various Sui mainnet RPC endpoints. At this time, we don't recommend using this RPC endpoint for mission-critical use cases. Suinfra is still in active development, and there could be occasional outages as we experiment with different configurations. Furthermore, operating this endpoint is not free, so we'll be exploring various ways to achieve financial sustainability over time.

```
https://rpc.suinfra.io
```

When sending a POST request to the Suinfra RPC endpoint, you'll receive a response with a few additional Suinfra-specific headers.

```
curl -X POST https://rpc.suinfra.io -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "sui_getObject", "params": ["0x521be8019b4c4943dee0f127af20b6811a069da2b71cc7faf8d420c30f5038ed"], "id":1}' -s -D - -o /dev/null

HTTP/2 200
date: Fri, 07 Jun 2024 02:37:49 GMT
content-type: application/json; charset=utf-8
access-control-expose-headers: access-control-allow-origin, vary, content-length, date, content-type
access-control-allow-origin: *
vary: access-control-request-headers, Origin, Access-Control-Request-Method, Access-Control-Request-Headers
x-routed-by: nrt:e78432e0c17383
x-routed-from: nrt
x-routed-to: sui-mainnet-rpc-korea.allthatnode.com
x-server: suinfra
```

* `x-routed-by` refers to the specific server that processed the request. In the example above, `nrt:e78432e0c17383` translates to "the server with the ID `e78432e0c17383` located in `nrt` (the region code for Tokyo, Japan) processed this request".
* `x-routed-from` refers to the edge region where the request was received.
* `x-routed-to` refers to the destination RPC endpoint which the request was routed to.

