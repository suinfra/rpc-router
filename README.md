# Suinfra RPC Router

The Suinfra RPC Router is a globally distributed and geographically-aware proxy that routes RPC requests to the closest RPC endpoint.

## How it Works

Suinfra routinely conducts [RPC benchmark tests](https://suinfra.io/rpc/2d730281-e288-4c82-8abb-33e1a75968c5/) in 35 regions around the world. These benchmark results are also [available in JSON format](https://suinfra.io/api/v1/rpc/2d730281-e288-4c82-8abb-33e1a75968c5/) through the Suinfra API. With these benchmark results, we're able to objectively determine the fastest RPC endpoints in each region, and dynamically generate region-specific HAProxy configurations.

A base HAProxy configuration file can be found in `haproxy.cfg`. Within the base configuration file, there's a `<DYNAMIC_CONFIG>`variable that's replaced with region-specific backend information when running the `generate_region_configs.py` script. The `generate_region_configs.py` script fetches RPC results for the specified `SUINFRA_TEST_ID`, and dynamically generates HAProxy configuration files for each region, and stores them in `./region_configs`.

The proxy itself is designed to be deployed on [https://fly.io](Fly.io), an infrastructure provider that leverages [Anycast](https://fly.io/docs/networking/services/#anycast-ip-addresses) to route user requests to the closest Fly region. With this configuration, an RPC request from a user in Singapore will be routed to an HAProxy instance in Singapore, and then forwarded to the best-performing RPC endpoint from Singapore (based on Suinfra test results). Ultimately, this means users will be able to rely on a single RPC endpoint, no matter where they are in the world.