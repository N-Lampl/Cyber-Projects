# module-3 · network labs (TCP/IP · HTTP · DNS · TLS)

Hands-on foundations: **craft real wire-format packets, write them to a real `.pcap`, then
dissect them back** — all offline. I hand-roll Ethernet/IPv4/TCP/UDP/DNS/HTTP/TLS encoders
(pure stdlib `struct`/`socket`), generate a synthetic capture of one realistic web fetch, and
parse it into per-protocol counts and writeups. No live sniffing, no network.

**Authorized use only.** Everything here is synthetic traffic between
documentation/RFC-1918 addresses that *my own code* generates. No real hosts are contacted.
See [../../ETHICS.md](../../ETHICS.md).

## The idea

A packet is just nested headers. The labs make that concrete by building the stack bottom-up
and verifying it with the same checksums the Internet uses:

```
+--------------------------------------------------------------+
| Ethernet II  | dst MAC | src MAC | ethertype=0x0800          |  L2
|   +----------------------------------------------------------+
|   | IPv4     | ver/ihl | ttl | proto | checksum | src | dst  |  L3
|   |   +------------------------------------------------------+
|   |   | TCP/UDP | sport | dport | seq/ack | flags | cksum    |  L4
|   |   |   +--------------------------------------------------+
|   |   |   | DNS query / HTTP GET / TLS ClientHello ...       |  L7
+--------------------------------------------------------------+
```

The synthetic trace is one coherent conversation:

1. **DNS** (UDP/53): recursion-desired `A` query for `example.com` -> `A` answer.
2. **TCP** (`:80`): 3-way handshake `SYN -> SYN/ACK -> ACK`.
3. **HTTP/1.1**: cleartext `GET /index.html` -> `200 OK`, then `FIN/ACK` teardown.
4. **TLS** (`:443`): second flow, `ClientHello` (with SNI) -> `ServerHello`.

Correctness is enforced, not assumed: every IPv4 header and every TCP/UDP pseudo-header
**checksum re-sums to zero** (RFC 1071), which the tests assert.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run            # generates the pcap if missing, parses it, writes figures + metrics.json
make pcap           # just (re)generate data/synthetic.pcap
make test           # fast smoke tests

# optional enhanced engine (craft/parse with scapy instead of pure-python):
python3 scripts/make_pcap.py --engine scapy   # pip install scapy==2.5.0 first
python3 scripts/analyze.py   --engine scapy
```

**Offline by default.** The default path needs only `matplotlib` (everything else is stdlib);
it never touches the network. `scapy` is an *optional* enhancement, imported lazily inside a
`try/except`, so the package still imports and runs without it.

Outputs land in [results/](results/):
- `figures/protocol_breakdown.png` — packet counts at L3 / L4 / L7.
- `figures/flow_timeline.png` — the conversation as an ordered, labelled timeline.
- `metrics.json` — protocol/packet counts + headline facts (committed as evidence).

## What the result shows

The 16-packet capture exercises every protocol in the module and the parser recovers the
whole story from raw bytes: the DNS name and its answer, the TCP 3-way handshake (detected
from flags alone), the HTTP method/path/status, and the TLS handshake type — including the
SNI hostname that leaks *even under TLS*. That's the security punchline of the foundations
module: DNS and HTTP are fully observable on-path, and TLS still exposes the destination name,
which is exactly why DNSSEC/DoH, HTTPS, and ECH exist.

## Interview story (3 sentences)

> I built the network stack from scratch — hand-encoding Ethernet/IP/TCP/UDP/DNS/HTTP/TLS into
> real wire bytes, writing a valid `.pcap`, and dissecting it back — to prove I understand
> exactly what's on the wire rather than leaning on a library. The parser reconstructs the full
> DNS->TCP->HTTP->TLS conversation from raw bytes and verifies every Internet checksum, and it
> highlights that DNS/HTTP are cleartext and TLS still leaks the SNI hostname. The same
> byte-level fluency is what later lets me reason about packet-level evasion against an IDS.

## Layout

```
src/netlabs/   utils.py (seeds) · protocols.py (wire encoders + checksums) ·
               pcap.py (libpcap I/O) · generate.py (synthetic trace) · parse.py (dissector)
scripts/       make_pcap.py · analyze.py
tests/         test_smoke.py  (fast invariants + one @slow end-to-end)
results/       figures/*.png + metrics.json  (committed)
data/ models/  git-ignored (pcap produced at runtime; no models here)
```

## References

- RFC 791 (IPv4), RFC 793 (TCP), RFC 768 (UDP), RFC 1071 (Internet checksum).
- RFC 1035 (DNS), RFC 9110 (HTTP semantics), RFC 8446 (TLS 1.3), RFC 6066 (SNI).
- libpcap "classic" file format · scapy docs (https://scapy.readthedocs.io) for the optional engine.
