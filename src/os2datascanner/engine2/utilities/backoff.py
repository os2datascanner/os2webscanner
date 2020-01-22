from sys import stderr
from time import sleep


def run_with_backoff(
        op, *exception_set,
        count=0, max_tries=10, ceiling=6, base=1, warn_after=6):
    """Performs an operation until it succeeds (or until the maximum number of
    attempts is hit), with exponential backoff after each failure. On success,
    returns a (result, parameters) pair; expanding the parameters dictionary
    and giving it to this function will allow the backoff behaviour to be
    persistent."""
    count = max(0, count)
    base = max(0.01, base)
    end = count + max_tries
    while count < end:
        if count:
            max_delay = base * (2 ** (min(count, ceiling) - 1))
            sleep(max_delay)
        try:
            return (op(), dict(
                    count=count, max_tries=max_tries, ceiling=ceiling,
                    base=base))
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
                            " delaying for {2} seconds".format(
                                    str(op), count, max_delay),
                            file=stderr)
            else:
                # This is not a backoff exception -- raise it immediately
                raise
