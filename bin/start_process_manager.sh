#!/bin/bash

exec "`dirname "${BASH_SOURCE[0]}"`/manage-admin" process_manager "$@"
