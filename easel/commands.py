import logging
import sys

from easel import course
from easel import files
from easel import helpers
from easel import helpers_yaml

def cmd_login(db, args):
    hostname = args.hostname
    token = args.token

    protocol = "https://"
    if hostname.startswith(protocol):
            hostname = hostname[len(protocol):]
    if hostname.endswith("/"):
            hostname = hostname[:len(hostname)-1]

    helpers.write_config(hostname, token, args.dry_run)
    # TODO: should probably verify against the canvas api

def cmd_init(db, args):
    helpers.setup_directories(args.dry_run)

def cmd_course(db, args):
    if args.subcommand == "list":
        cmd_course_list(db)
    elif args.subcommand == "add":
        if args.subcommand_argument:
            cmd_course_add(db, args.subcommand_argument, args.dry_run)
        else:
            print("add subcommand requires the course url to add")
    elif args.subcommand == "remove":
        if args.subcommand_argument:
            cmd_course_remove(db, args.subcommand_argument, args.dry_run)
        else:
            print("remove subcommand requires a search term for the course url"
                    " to be removed")

def cmd_course_list(db):
    courses = course.find_all(db)
    for course_ in courses:
        print(course_)

def cmd_course_add(db, course_url, dry_run):
    #conf = helpers.load_config()
    course_id = course.get_id_from_url(course_url)
    if len(course.find(db, course_id)) > 0:
        print(f"course {course_id} already exists in the db")
        sys.exit(1)

    c = course.pull(db, course_id)
    if dry_run:
        print(f"DRYRUN - saving course {c}")
    else:
        c.save(db)

def cmd_course_remove(db, course_search, dry_run):
    courses = course.match_course(db, course_search)
    if len(courses) == 0:
        print("could not find course for", course_search)
        sys.exit(1)
    elif len(courses) > 1:
        for course_ in courses:
            print(course_)
        print("the search found more than one course")
        print("   pick the correct course id from the list")
        print("   and run 'easel course remove <id>'")
        sys.exit(1)

    if dry_run:
        print(f"DRYRUN - removing course {courses[0]}")
    else:
        courses[0].remove(db)
        print("removed course", courses[0].name)

def cmd_remove(db, args):
    if not args.components:
        print("TODO: remove everything")
    else:
        if not args.course:
            args.course = course.find_all(db)
        else:
            args.course = course.match_courses(db, args.course)

        for component_filepath in args.components:
            for course_ in args.course:
                if component_filepath == "syllabus.md":
                    logging.error("Don't remove your syllabus!")
                else:
                    component = helpers_yaml.read(component_filepath)
                    if component and not isinstance(component, str):
                        component.filename = component_filepath
                        print(f"removing {component} from {course_.name} ({course_.canvas_id})")
                        component.remove(db, course_, args.dry_run)
                    else:
                        # not a yaml file so assume it's a file/dir to remove
                        files.remove(db, course_, component_filepath, args.dry_run)

def cmd_pull(db, args):
    if not args.components:
        print("TODO: pull everything")
    else:
        print("TODO: pull", args.components)

def cmd_push(db, args):
    if not args.components:
        print("TODO: push everything")
    else:
        if not args.course:
            args.course = course.find_all(db)
        else:
            args.course = course.match_courses(db, args.course)

        for component_filepath in args.components:
            for course_ in args.course:
                if component_filepath == "syllabus.md":
                    print(f"pushing syllabus to {course_.name} ({course_.canvas_id})")
                    course.push_syllabus(db, course_.canvas_id, args.dry_run)
                else:
                    component = helpers_yaml.read(component_filepath)
                    if component and not isinstance(component, str):
                        component.filename = component_filepath
                        print(f"pushing {component} to {course_.name} ({course_.canvas_id})")
                        component.push(db, course_.canvas_id, args.dry_run)
                    else:
                        # not a yaml file so assume it's a file/dir to upload
                        files.push(db, course_, component_filepath,
                                args.hidden, args.dry_run)
