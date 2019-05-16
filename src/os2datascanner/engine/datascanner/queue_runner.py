#!/usr/bin/env python3

import argparse

from .model.zip import ZipSource
from .model.core import Source, SourceManager, UnknownSchemeError
from .model.file import FilesystemSource
from .processors import processors

from queue import Full, Empty
from ctypes import c_ulong
from datetime import datetime
from traceback import print_exc
from multiprocessing import Value, Manager, Process, current_process

queue = []

done = "__SENTINEL__FINISHED__"

def put(queue, what, renderer=str):
    me = current_process().name
    seconds = 0
    while True:
        try:
            queue.put(what, True, 1)
            print("{0} put {1}".format(me, renderer(what)))
            break
        except Full:
            seconds += 1
            print("{0} write-spinning for {1} seconds...".format(me, seconds))

def take(queue, renderer=str):
    me = current_process().name
    seconds = 0
    while True:
        try:
            i = queue.get(True, 1)
            print("{0} took {1}".format(me, renderer(i)))
            return i
        except Empty:
            seconds += 1
            print("{0} read-spinning for {1} seconds...".format(me, seconds))

def generate(start, urls, sources):
    count = 0
    try:
        for url in urls:
            try:
                put(sources, Source.from_url(url))
                count += 1
            except UnknownSchemeError:
                pass
    finally:
        sources.put(done)
        now = (datetime.now() - start).total_seconds()
        per_sec = float(count) / now
        print(("generate signing off after finding {0} sources in {1} " +
                "seconds ({2} sources/sec)").format(count, now, per_sec))

def explore(start, sm, sources, handles):
    count = 0
    total = 0
    own_sources = []
    try:
        while True:
            source = None
            if own_sources:
                source = own_sources[0]
                own_sources = own_sources[1:]
            else:
                source = take(sources)
                if source == done:
                    break
            for handle in source.handles(sm):
                derived_source = Source.from_handle(handle)
                if derived_source:
                    own_sources.append(derived_source)
                else:
                    t = handle.guess_type()
                    if t in processors:
                        put(handles, handle)
                        count += 1
                total += 1
    finally:
        now = (datetime.now() - start).total_seconds()
        per_sec = float(count) / now
        print(("explore signing off after finding {0} handles (out of {3}) " +
                "in {1} seconds ({2} handles/sec)").format(
                    count, now, per_sec, total))
        put(handles, done)

def print_handle_name(tpl):
    return "<text from {0}>".format(tpl[0])

def process(start, parent, handles, texts, peers):
    with peers.get_lock():
        peers.value += 1
    me = current_process().name
    count = 0
    try:
        with SourceManager(parent) as sm:
            while True:
                handle = take(handles)
                if handle == done:
                    put(handles, done)
                    break
                else:
                    r = handle.follow(sm)
                    type = handle.guess_type()
                    print("{0}: beginning {1} ({2})".format(me, handle, type))
                    try:
                        text = processors[type](r)
                    except Exception:
                        print_exc()
                        text = None
                    if text:
                        print("{0}: finished {1}, got some text".format(
                                me, handle))
                        put(texts, ((handle, text)), print_handle_name)
                        count += 1
                    else:
                        print("{0}: finished {1}, no good".format(me, handle))
    finally:
        now = (datetime.now() - start).total_seconds()
        per_sec = float(count) / now
        print(("{3} signing off after generating {0} texts in " +
               "{1} seconds ({2} texts/sec)").format(count, now, per_sec, me))
        with peers.get_lock():
            peers.value -= 1
            if not peers.value:
                print("{0} is the last processor, sending sentinel".format(me))
                put(texts, done)
            else:
                print("{0} was not the last processor, {1} remain".format(
                        me, peers.value))

def display(start, texts):
    count = 0
    try:
        while True:
            text = take(texts, print_handle_name)
            if text == done:
                finished = True
                break
            else:
                handle, txt = text
                if txt:
                    print(handle, txt[:128])
                count += 1
    finally:
        now = (datetime.now() - start).total_seconds()
        per_sec = float(count) / now
        print(("display signing off after printing {0} texts in {1} " +
                "seconds ({2} texts/sec)").format(count, now, per_sec))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "urls",
            metavar="URL", nargs='+')

    args = parser.parse_args()
    with Manager() as manager:
        sources = manager.Queue()
        handles = manager.Queue()
        texts = manager.Queue()
        processor_c = Value(c_ulong, 0)

        start = datetime.now()

        with SourceManager() as sm:
            # Collect all of the handles in advance so that downloading file
            # content doesn't starve other parts of the system
            generate(start, args.urls, sources)
            explore(start, sm, sources, handles)

            start = datetime.now()
            processor_handles = [
                Process(target=process, name="processor{0}".format(i),
                        args=(start, sm.share(), handles, texts, processor_c,))
                for i in range(0, 3)]
            display_handle = Process(
                    target=display, name="display", args=(start, texts,))

            try:
                display_handle.start()
                [h.start() for h in processor_handles]

                def wait_on(p):
                    while True:
                        print("waiting on {0}".format(p))
                        p.join()
                        if p.exitcode != None:
                            print("joined {0}".format(p))
                            break

                [wait_on(h) for h in processor_handles]
                wait_on(display_handle)
                duration = (datetime.now() - start).total_seconds()
                print("Everything finished after {0} seconds.".format(duration))
            except BaseException:
                print("Uncaught exception: joining all children to shut " +
                        "down context manager cleanly.")
                [wait_on(h) for h in processor_handles]
                wait_on(display_handle)
                duration = (datetime.now() - start).total_seconds()
                print("Unclean shutdown after {0} seconds.".format(duration))
                raise

if __name__ == '__main__':
    main()
