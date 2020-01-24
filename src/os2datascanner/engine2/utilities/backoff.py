from sys import stderr
from time import sleep
from random import random


def run_with_backoff(
        op, *exception_set,
        count=0, max_tries=10, ceiling=7, base=1, warn_after=6, fuzz=0):
    """Performs an operation until it succeeds (or until the maximum number of
    attempts is hit), with exponential backoff after each failure. On success,
    returns a (result, parameters) pair; expanding the parameters dictionary
    and giving it to this function will allow the backoff behaviour to be
    persistent."""
    count = max(0, int(count))
    base = max(0.01, base)
    end = count + max_tries
    fuzz = max(min(fuzz or 0, 1), 0)
    while count < end:
        if count:
            max_delay = base * (2 ** (min(count, ceiling) - 1))
            if fuzz:
                # Sleep time is randomly adjusted by the proportion given in
                # the fuzz parameter (0 - 0% adjustment, 1 - ±100% adjustment)
                fuzz_diff = (max_delay * fuzz)
                adj = -fuzz_diff + (2 * random() * fuzz_diff)
                print(fuzz, fuzz_diff, adj, max_delay)
                max_delay += adj
            sleep(max_delay)
        try:
            return (op(), dict(
                    count=count, max_tries=max_tries, ceiling=ceiling,
                    base=base, fuzz=fuzz))
        except Exception as e:
            if isinstance(e, exception_set):
                # This exception indicates that we should back off and try
                # again
                count += 1
                if count == max_tries:
                    # ... but we've exhausted our maximum attempts
                    if warn_after and count >= warn_after:
                        print("warning: while executing {0}"
                                " with backoff: failed {1} times,"
                                " giving up".format(
                                        str(op), count),
                                file=stderr)
                    raise
                elif warn_after and count >= warn_after:
                    max_delay = base * (2 ** (min(count, ceiling) - 1))
                    print("warning: while executing {0}"
                            " with backoff: failed {1} times,"
                            " delaying for {2}±{3:.1f} seconds".format(
                                    str(op), count, max_delay,
                                    max_delay * fuzz),
                            file=stderr)
            else:
                # This is not a backoff exception -- raise it immediately
                raise
