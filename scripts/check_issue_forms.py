#!/usr/bin/env python3
"""Validate the issue-form subset used here and its label/documentation references.

Install development dependencies with python -m pip install -r requirements-dev.txt.
This is a local structural check. GitHub's rendered chooser is checked separately
after publishing these files to the default branch. No GitHub changes are made.
"""
import argparse
import json
from pathlib import Path
import re

try:
    import yaml
except ImportError:
    raise SystemExit('Install development dependencies: python -m pip install -r requirements-dev.txt')

ROOT = Path(__file__).resolve().parents[1]
WIKI = 'https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/'
FORMS = {
    '01-bug-report.yml': 'bug',
    '02-feature-request.yml': 'enhancement',
    '03-translation-problem.yml': 'translation',
    '04-documentation-correction.yml': 'documentation',
    '05-question.yml': 'question',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class UniqueLoader(yaml.SafeLoader):
    """A duplicate YAML key must fail instead of silently changing a form."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(isinstance(key,str), 'YAML mapping keys must be strings')
        require(key not in result, f'Duplicate YAML mapping key at line {key_node.start_mark.line+1}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,unique_mapping)


def load_yaml(path):
    return yaml.load(Path(path).read_text(encoding='utf-8'),Loader=UniqueLoader)


def text(value):
    return isinstance(value,str) and bool(value.strip())


def validate(root=ROOT):
    root = Path(root)
    labels = json.loads((root/'.github/labels.json').read_text(encoding='utf-8'))
    require(isinstance(labels,list) and labels, 'Label catalog must be a nonempty list')
    names = set()
    for index,label in enumerate(labels):
        location = f'Label {index+1}'
        require(isinstance(label,dict) and set(label)=={'name','color','description'},location+': unexpected metadata')
        name = label['name']
        require(text(name) and name==name.strip() and len(name)<=50,location+': invalid name')
        require(name.casefold() not in names,location+': duplicate name')
        names.add(name.casefold())
        require(isinstance(label['color'],str) and re.fullmatch(r'[0-9a-f]{6}',label['color']),location+': invalid color')
        require(text(label['description']) and len(label['description'])<=100,location+': invalid description')
    templates = root/'.github/ISSUE_TEMPLATE'
    require({p.name for p in templates.iterdir()}==set(FORMS)|{'config.yml'},'Unexpected issue-template files')
    form_names = set()
    for filename,category in FORMS.items():
        form = load_yaml(templates/filename)
        require(isinstance(form,dict) and set(form)=={'name','description','labels','body'},filename+': invalid form keys')
        require(text(form['name']) and 3<len(form['name'])<=64,filename+': invalid form name')
        require(form['name'] not in form_names,filename+': duplicate form name')
        form_names.add(form['name'])
        require(text(form['description']) and len(form['description'])<=200,filename+': invalid description')
        require(isinstance(form['labels'],list) and set(form['labels'])=={category,'needs-triage'},filename+': incorrect automatic labels')
        require(all(name in names for name in form['labels']),filename+': unknown automatic label')
        body = form['body']
        require(isinstance(body,list) and body,filename+': empty form')
        ids = set()
        field_labels = set()
        for index,element in enumerate(body):
            location = f'{filename}: element {index+1}'
            require(isinstance(element,dict) and set(element)<={'type','id','attributes','validations'},location+': invalid element keys')
            kind = element.get('type')
            require(kind in {'markdown','input','textarea','dropdown','checkboxes'},location+': unsupported element')
            attributes = element.get('attributes')
            require(isinstance(attributes,dict),location+': missing attributes')
            if kind=='markdown':
                require(set(attributes)=={'value'} and text(attributes['value']),location+': invalid markdown')
                continue
            identity = element.get('id')
            require(isinstance(identity,str) and re.fullmatch(r'[a-zA-Z0-9_-]+',identity),location+': invalid field ID')
            require(identity not in ids,location+': duplicate field ID')
            ids.add(identity)
            allowed = {'label','description'} | {
                'input': {'placeholder','value'}, 'textarea': {'placeholder','value','render'},
                'dropdown': {'multiple','options'}, 'checkboxes': {'options'},
            }[kind]
            require(set(attributes)<=allowed and text(attributes.get('label')),location+': invalid field attributes')
            require(attributes['label'].casefold() not in field_labels,location+': duplicate field label')
            field_labels.add(attributes['label'].casefold())
            validations = element.get('validations',{})
            require(isinstance(validations,dict) and set(validations)<={'required'} and
                    ('required' not in validations or type(validations['required']) is bool),location+': invalid required flag')
            if kind=='dropdown':
                options = attributes.get('options')
                require(isinstance(options,list) and len(options)>1 and all(text(v) for v in options),location+': invalid dropdown options')
                require(len(set(options))==len(options) and 'None' not in options,location+': duplicate or reserved option')
                require('multiple' not in attributes or type(attributes['multiple']) is bool,location+': invalid multiple flag')
            if kind=='checkboxes':
                options = attributes.get('options')
                require(isinstance(options,list) and options,location+': missing checkbox options')
                require(all(isinstance(v,dict) and set(v)=={'label','required'} and text(v['label']) and
                            type(v['required']) is bool for v in options),location+': invalid checkbox options')
                require(len({v['label'] for v in options})==len(options),location+': duplicate checkbox labels')
            if identity in {'logs','screenshots','screenshot'}:
                require(validations.get('required') is False,location+': diagnostics must remain optional')
                if identity!='logs':
                    require('render' not in attributes,location+': screenshots need attachment support')
        source = (templates/filename).read_text(encoding='utf-8')
        require('public' in source and 'private' in source,filename+': missing public/privacy guidance')
        for page in re.findall(re.escape(WIKI)+r'([A-Za-z-]+)',source):
            require((ROOT/'docs/wiki'/f'{page}.md').is_file(),filename+': unknown wiki reference')
    config = load_yaml(templates/'config.yml')
    require(isinstance(config,dict) and set(config)=={'blank_issues_enabled','contact_links'} and
            config['blank_issues_enabled'] is False,'Blank-issue configuration must be disabled')
    links = config['contact_links']
    require(isinstance(links,list) and len(links)==3,'Expected three documentation contact links')
    expected_pages = {'Getting-Started','Troubleshooting','Diagnostics-and-Support'}
    require({link.get('url') for link in links}=={WIKI+p for p in expected_pages},'Incorrect contact-link destinations')
    for link in links:
        require(set(link)=={'name','url','about'} and all(text(v) for v in link.values()),'Invalid contact link')
    return len(FORMS),len(labels)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    count,label_count = validate(parser.parse_args().root)
    print(f'PASS: {count} issue forms, {label_count} label definitions, automatic labels, field structure, privacy guidance, and chooser links.')
