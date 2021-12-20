import argparse
import logging

from easel import commands
from easel import helpers

def main():
    parser = argparse.ArgumentParser(prog="easel", description="Easel - A Canvas "
            "course management tool.")

    # flags
    parser.add_argument('--api', action='store_true', help="report all API "
            "requests")
    parser.add_argument('--api-dump', action='store_true', help="dump API request "
            "and response data")
    parser.add_argument('--dry-run', action='store_true', help="try executing "
            "the command without actually making any write requests to canvas "
            "or the db")
    parser.add_argument('--course', '-c', action='append', help="the canvas "
            "course(s) on which to perform the action")
    parser.add_argument('--hidden', action='store_true', help="when pushing "
            "the given component, do not publish it")

    # commands
    subparsers = parser.add_subparsers(dest="command", help="the easel action to "
            "perform")
    subparsers.required = True

    ## logging in
    parser_login = subparsers.add_parser("login", help="login to Canvas")
    parser_login.add_argument("hostname", help="the hostname of your Canvas "
            "instance")
    parser_login.add_argument("token", help="your api token")
    parser_login.set_defaults(func=commands.cmd_login)

    ## init
    parser_init = subparsers.add_parser("init", help="initialize the db")
    parser_init.set_defaults(func=commands.cmd_init)

    ## course commands
    parser_course = subparsers.add_parser("course", help="course management "
            "commands")
    parser_course.add_argument("subcommand", choices=["list", "add", "remove"])
    parser_course.add_argument("subcommand_argument", nargs="?")
    parser_course.set_defaults(func=commands.cmd_course)

    component_arg = "components"

    ## pull
    parser_pull = subparsers.add_parser("pull", help="pull components")
    parser_pull.add_argument(component_arg, nargs="*", help="the specific "
            "component(s) to pull")
    parser_pull.set_defaults(func=commands.cmd_pull)

    ## push
    parser_push = subparsers.add_parser("push", help="push components")
    parser_push.add_argument(component_arg, nargs="*", help="the specific "
            "component(s) to push")
    parser_push.set_defaults(func=commands.cmd_push)

    ## remove
    parser_remove = subparsers.add_parser("remove", help="remove components")
    parser_remove.add_argument(component_arg, nargs="*", help="the specific "
            "component(s) to remove")
    parser_remove.set_defaults(func=commands.cmd_remove)

    ## md preview
    parser_md = subparsers.add_parser("md", help="preview the relevant text "
            "field of the given component(s) converted to html")
    parser_md.add_argument(component_arg, nargs="*", help="the specific "
            "component(s) to convert to html")
    parser_md.set_defaults(func=commands.cmd_md)

    ###################################

    args = parser.parse_args()

    if args.api:
        logging.basicConfig(level=logging.INFO)
    elif args.api_dump:
        logging.basicConfig(level=logging.DEBUG)

    db = helpers.load_db()
    args.func(db, args)
    db.close()

if __name__ == "__main__":
    main()
