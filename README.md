# tpe_prio

Use like a regular `concurrent.futures.ThreadPoolExecutor` except there is now a
`bump(fut)` method.  During execution, the deque gets rotated and put back, so
it is possible that workers will pick up a non-optimal next choice for a small
window of time.


# License

tpe_prio is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
