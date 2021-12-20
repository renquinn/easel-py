import importlib
import logging
import os.path
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

    if not helpers.write_config(hostname, token, args.dry_run):
        return

    # confirm user logged in correctly
    resp = helpers.get("/api/v1/users/self")
    if resp and isinstance(resp, dict) and "name" in resp and resp["name"]:
        print("Found user:", resp['name'])
    else:
        logging.error("There was an issue logging you in. Check the hostname "
                "of your canvas instance as well as your token.")
        logging.debug(resp)

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
        # remove everything
        args.components = ["modules", "assignments", "files", "pages",
                "quizzes", "assignment_groups"]

    if not args.course:
        args.course = course.find_all(db)
    else:
        args.course = course.match_courses(db, args.course)

    for component_filepath in args.components:
        if component_filepath.endswith("*"):
            component_filepath = component_filepath[:-1]
        if component_filepath.endswith("/"):
            component_filepath = component_filepath[:-1]

        if os.path.isdir(component_filepath) and not component_filepath.startswith("files"):
            if component_filepath not in helpers.DIRS:
                logging.error("Invalid directory: "+component_filepath)
                continue

            for child_path in os.listdir(component_filepath):
                full_child_path = component_filepath + '/' + child_path
                component = helpers_yaml.read(full_child_path)
                if component and not isinstance(component, str):
                    component.filename = full_child_path
                    for course_ in args.course:
                        print(f"removing {component} from {course_.name} ({course_.canvas_id})")
                        component.remove(db, course_, args.dry_run)
        else:
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
        # pull everything
        args.components = ["assignment_groups", "assignments", "files",
                "pages", "quizzes", "modules"]

    if not args.course:
        args.course = course.find_all(db)
    else:
        args.course = course.match_courses(db, args.course)

    for component_filepath in args.components:
        local = {}
        remote = {}

        if component_filepath.endswith("*"):
            component_filepath = component_filepath[:-1]
        if component_filepath.endswith("/"):
            component_filepath = component_filepath[:-1]

        if os.path.isdir(component_filepath):
            if component_filepath not in helpers.DIRS:
                logging.error("Invalid directory: "+component_filepath)
                break

            # local versions
            for child_path in os.listdir(component_filepath):
                if not component_filepath.startswith("files"):
                    component = helpers_yaml.read(component_filepath + '/' +
                            child_path)
                    local[component.filename] = component

            # request remote versions
            for course_ in args.course:
                m = importlib.import_module("easel."+helpers.DIRS[component_filepath])
                print(f"pulling all {component_filepath} from {course_.name} ({course_.canvas_id})")
                for remote_comp in m.pull_all(db, course_, args.dry_run):
                    if remote_comp.filename in remote:
                        remote[remote_comp.filename].append(remote_comp)
                    else:
                        remote[remote_comp.filename] = [remote_comp]

        elif os.path.isfile(component_filepath):
            # local version
            component = helpers_yaml.read(component_filepath)
            component.filename = component_filepath
            local[component.filename] = component

            # request remote version(s)
            for course_ in args.course:
                print(f"pulling {component} from {course_.name} ({course_.canvas_id})")
                remote_comp = component.pull(db, course_, args.dry_run)
                if remote_comp.filename in remote:
                    remote[remote_comp.filename].append(remote_comp)
                else:
                    remote[remote_comp.filename] = [remote_comp]

        else:
            logging.error("Cannot find file: " + component_filepath)

        # TODO: merge remote into local
        for remote_comp in remote:
            components = remote[remote_comp]
            if remote_comp in local:
                logging.warn("Overwriting local copy of "
                        "{components[0].filename}. In the future, we'll "
                        "implement a merge workflow")
            if len(remote[remote_comp]) == 1:
                print(f"writing {components[0]} to {components[0].filename}")
                helpers_yaml.write(components[0].filename, components[0])
            else:
                logging.error("Too many remote options to handle right now..."
                        "Please manually specify a single course to pull from "
                        "with the -c flag and later we'll implement a merge "
                        "workflow")

def cmd_push(db, args):
    if not args.components:
        # push everything
        args.components = ["syllabus.md", "assignment_groups", "assignments",
                "files", "pages", "quizzes", "modules"]

    if not args.course:
        args.course = course.find_all(db)
    else:
        args.course = course.match_courses(db, args.course)

    for component_filepath in args.components:
        if component_filepath.endswith("*"):
            component_filepath = component_filepath[:-1]
        if component_filepath.endswith("/"):
            component_filepath = component_filepath[:-1]

        if os.path.isdir(component_filepath) and not component_filepath.startswith("files"):
            if component_filepath not in helpers.DIRS:
                logging.error("Invalid directory: "+component_filepath)
                continue

            for child_path in os.listdir(component_filepath):
                full_child_path = component_filepath + '/' + child_path
                component = helpers_yaml.read(full_child_path)
                if component and not isinstance(component, str):
                    component.filename = full_child_path
                    for course_ in args.course:
                        print(f"pushing {component} to {course_.name} ({course_.canvas_id})")
                        component.push(db, course_, args.dry_run)

        elif component_filepath.startswith("files"):
            for course_ in args.course:
                files.push(db, course_, component_filepath, args.hidden,
                        args.dry_run)
        else:
            for course_ in args.course:
                if component_filepath == "syllabus.md":
                    print(f"pushing syllabus to {course_.name} ({course_.canvas_id})")
                    course.push_syllabus(db, course_.canvas_id, args.dry_run)
                else:
                    component = helpers_yaml.read(component_filepath)
                    if component and not isinstance(component, str):
                        component.filename = component_filepath
                        print(f"pushing {component} to {course_.name} ({course_.canvas_id})")
                        component.push(db, course_, args.dry_run)
                    else:
                        # not a yaml file so assume it's a file/dir to upload
                        files.push(db, course_, component_filepath,
                                args.hidden, args.dry_run)

def cmd_md(db, args):
    if not args.components:
        args.components = ["syllabus.md", "assignment_groups", "assignments",
                "files", "pages", "quizzes", "modules"]

    for component_filepath in args.components:
        if component_filepath.endswith("*"):
            component_filepath = component_filepath[:-1]
        if component_filepath.endswith("/"):
            component_filepath = component_filepath[:-1]

        if os.path.isdir(component_filepath) and not component_filepath.startswith("files"):
            if component_filepath not in helpers.DIRS:
                logging.error("Invalid directory: "+component_filepath)
                continue

            for child_path in os.listdir(component_filepath):
                full_child_path = component_filepath + '/' + child_path
                component = helpers_yaml.read(full_child_path)
                print(component.md())
        else:
            if component_filepath == "syllabus.md":
                f = open("syllabus.md")
                print(helpers.md2html(f.read()))
                f.close()
            else:
                component = helpers_yaml.read(component_filepath)
                if isinstance(component, list):
                    for obj in component:
                        print("\n\n*****\n", obj.md())
                else:
                    print(component.md())
