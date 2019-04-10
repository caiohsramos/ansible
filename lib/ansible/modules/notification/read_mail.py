#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the sample module generates
    type: str
    returned: always
'''
import imaplib
import email

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        ssl=dict(type='bool', required=False, default=True),
        port=dict(type='int', required=False, default=None)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        username='',
        host='',
        password='',
        ssl='',
        list=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    # if module.params['name'] == 'fail me':
    #     module.fail_json(msg='You requested this to fail', **result)

    # create connection
    try:
        if module.params['ssl']:
            port = 993 if module.params['port'] is None else module.params['port']
            M = imaplib.IMAP4_SSL(module.params['host'], port=port)
        else:
            port = 143 if module.params['port'] is None else module.params['port']
            M = imaplib.IMAP4(module.params['host'], port=port)
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    # login
    try:
        M.login(module.params['username'], module.params['password'])
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    M.list()
    M.select('inbox')
    err, search = M.search(None, 'SUBJECT', '"Alerta"')
    if err != 'OK':
        module.fail_json(msg='Error', **result)

    for email_id in search[0].split():
        # last_email_id = search[0].split()[-1]
        err, body = M.fetch(email_id, '(RFC822)')
        if err != 'OK':
            module.fail_json(msg='Error', **result)

        msg = email.message_from_bytes(body[0][1])
        print(msg['to'])
        print(msg['from'])
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
