# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from Records import read_record
from SharedQueue.Report import queue_status
from SharedQueue.State import configure
from SharedQueue.Submit import cancel, enqueue


# existing controller forwarding makes shared scheduling available without a second launcher
def add_commands(commands):
    queued = commands.add_parser("enqueue")
    queued.add_argument("file")
    cancelled = commands.add_parser("cancel-request")
    cancelled.add_argument("request")
    cancelled.add_argument("--revision", type=int, required=True)
    status = commands.add_parser("queue-status")
    status.add_argument("--request")
    status.add_argument("--after")
    config = commands.add_parser("queue-config")
    config.add_argument("--max-pending", type=int, required=True)


# shared queue operations remain inside the controller transaction and owner fence
def dispatch(ledger, args):
    if args.command == "enqueue":
        return enqueue(ledger, read_record(args.file))
    if args.command == "cancel-request":
        return cancel(ledger, args.request, args.revision)
    if args.command == "queue-config":
        return configure(ledger, args.max_pending)
    return queue_status(ledger, args.request, args.after)
