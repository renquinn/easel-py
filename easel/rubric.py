import json
import logging
import yaml
from tqdm import tqdm

from easel import canvas_id
from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

RUBRICS_PATH = course.COURSE_PATH + "/rubrics"
RUBRIC_PATH = RUBRICS_PATH + "/{}"
RUBRICS_TABLE = "rubrics"
RUBRICS_DIR = "rubrics"

class Rubric(component.Component):

    def __init__(self, title=None, free_form_criterion_comments=None,
            criteria=None, points_possible=None, rubric_association=None,
            filename="", yaml_order=[]):
        super().__init__(create_path=RUBRICS_PATH,
                update_path=RUBRIC_PATH, db_table=RUBRICS_TABLE,
                filename=filename, yaml_order=yaml_order)
        self.title = title
        self.free_form_criterion_comments = free_form_criterion_comments
        self.criteria = criteria
        self.points_possible = points_possible
        self.rubric_association = rubric_association

    def __repr__(self):
        return f"Rubric(title={self.title}, points_possible={self.points_possible})"

    def yaml(self):
        """Override yaml method to ensure rubric data is not double-wrapped"""
        fields = dict(self.gen_fields())

        # Reorder fields according to original ordering from the yaml file
        ordered = {}
        if not self.yaml_order:
            ordered = fields
        else:
            for key in self.yaml_order:
                if key in fields:
                    ordered[key] = fields[key]

        return yaml.dump(ordered, sort_keys=False)

    def preprocess(self, db, course_, dry_run):
        # Canvas may require rubrics to be associated when created
        # If no rubric_association is specified, create a default one for the course
        if not self.rubric_association:
            self.rubric_association = {
                "association_id": course_.canvas_id,
                "association_type": "Course",
                "purpose": "bookmark",
                "use_for_grading": 0,
                "hide_score_total": 0
            }

    def __iter__(self):
        # Custom iteration to wrap fields in 'rubric' wrapper as required by Canvas API
        fields = dict(self.gen_fields())

        # Extract rubric_association if present
        rubric_association = fields.pop('rubric_association', None)

        # Remove points_possible - Canvas calculates this from criteria
        fields.pop('points_possible', None)

        # Convert criteria array to hash format expected by Canvas
        if 'criteria' in fields and isinstance(fields['criteria'], list):
            criteria_hash = {}
            for idx, criterion in enumerate(fields['criteria']):
                # Ensure criterion has an id (use Canvas-style underscore prefix)
                if 'id' not in criterion:
                    criterion['id'] = f'_{idx}'

                # Ensure criterion_use_range is set as string
                if 'criterion_use_range' not in criterion:
                    criterion['criterion_use_range'] = "false"
                elif isinstance(criterion['criterion_use_range'], bool):
                    criterion['criterion_use_range'] = "true" if criterion['criterion_use_range'] else "false"

                # Process ratings - convert array to hash with numeric string keys
                if 'ratings' in criterion and isinstance(criterion['ratings'], list):
                    ratings_hash = {}
                    for rating_idx, rating in enumerate(criterion['ratings']):
                        if 'id' not in rating:
                            # Use Canvas-style simple IDs
                            rating['id'] = f'rating_{rating_idx}' if rating_idx == 0 else f'rating_{rating_idx}_{idx}'
                        # Remove criterion_id - not needed in ratings hash
                        rating.pop('criterion_id', None)
                        # Remove empty long_description fields
                        if 'long_description' in rating and not rating['long_description']:
                            del rating['long_description']

                        # Add to ratings hash with 1-indexed keys
                        ratings_hash[str(rating_idx + 1)] = rating

                    criterion['ratings'] = ratings_hash

                # Use 1-indexed keys for criteria
                criteria_hash[str(idx + 1)] = criterion
            fields['criteria'] = criteria_hash

        # Add skip_updating_points_possible flag
        fields['skip_updating_points_possible'] = "false"

        # Wrap in 'rubric' key
        wrapped = {"rubric": fields}

        # Add rubric_association at the same level as 'rubric' if provided
        if rubric_association:
            wrapped['rubric_association'] = rubric_association

        yield from wrapped.items()

    @classmethod
    def build(cls, fields):
        defaults = {
            "free_form_criterion_comments": False,
        }

        # Debug: log what fields we're receiving
        logging.debug(f"Rubric.build received fields: {json.dumps(fields, indent=2, default=str)}")

        desired_fields = cls.__init__.__code__.co_varnames[1:]

        # Convert Canvas API 'data' field to 'criteria' BEFORE filtering
        if 'data' in fields and fields['data']:
            # Canvas returns criteria as a hash with numeric string keys
            # Convert to array for cleaner YAML
            if isinstance(fields['data'], dict):
                criteria_array = []
                for key in sorted(fields['data'].keys(), key=lambda x: int(x) if x.isdigit() else 0):
                    criteria_array.append(fields['data'][key])
                fields['criteria'] = criteria_array
            else:
                fields['criteria'] = fields['data']
            del fields['data']

        component.filter_fields(fields, desired_fields, defaults)

        return Rubric(**fields)


# Needed for custom yaml tag
def constructor(loader, node):
    fields = helpers_yaml.construct_ordered_mapping(loader, node)
    return Rubric(**fields)

def pull(db, course_, rubric_id, dry_run):
    course_id = course_.canvas_id
    resp = helpers.get(RUBRIC_PATH.format(course_id, rubric_id), dry_run=dry_run)

    # Canvas returns rubrics in a special format: {'rubric': {...}, 'rubric_association': {...}}
    if 'rubric' in resp:
        r = resp['rubric']
        # Optionally preserve rubric_association if present
        if 'rubric_association' in resp:
            r['rubric_association'] = resp['rubric_association']
    else:
        r = resp

    if not r.get('id'):
        logging.error(f"Rubric {rubric_id} does not exist for course {course_id}")
        return None, None

    cid = canvas_id.find_by_id(db, course_id, r.get('id'))
    if cid:
        r['filename'] = cid.filename
    else:
        r['filename'] = component.gen_filename(RUBRICS_DIR, r.get('title', ''))
        cid = canvas_id.CanvasID(r['filename'], course_id)
        cid.canvas_id = r.get('id')
        cid.save(db)

    return Rubric.build(r), cid

def pull_all(db, course_, dry_run):
    r = helpers.get(RUBRICS_PATH.format(course_.canvas_id), dry_run=dry_run)
    rubrics = []
    print("pulling rubric contents")
    for rubric in tqdm(r):
        rubric_, _ = pull(db, course_, rubric.get('id'), dry_run)
        if rubric_:
            rubrics.append(rubric_)
    return rubrics
