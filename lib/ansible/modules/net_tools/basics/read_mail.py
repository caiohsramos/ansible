#!/usr/bin/python

# Copyright: (c) 2018, Caio Ramos <caioramos97@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: read_mail

short_description: Module for reading emails from a IMAP server

version_added: "2.9"

description:
    - Get emails from a IMAP server using basic filtering rules and returns
      the email count and a list of dictionaries where each represents an email
      that satisfied the filters. This module is intended to be used by other
      tasks that take actions depending on the result of the emails.

options:
    host:
        description:
            - IMAP server host
        required: false
        default: localhost
    port:
        description:
            - IMAP server port (defaults to 993, if TLS is chosen, or 143 if not)
        required: false
        default: -1
    username:
        description:
            - Username to get the emails
        required: true
    password:
        description:
            - Password to get the emails
        required: true
    tls:
        description:
            - Whether to use TLS connection or not
        required: false
        default: true
    mailbox:
        description:
            - Select the mailbox to use
        required: false
        default: INBOX
    filter:
        description:
            - Default IMAP filters. Checkout the options at RFC 3501 section 6.4.4
        required: false
        default: {'ALL': ''}

author:
    - Caio Ramos (@caiohsramos)
    - Gabriely Rangel (@gprangel)
'''

EXAMPLES = r'''
- name: Read mails from "imap.myhost.com" with default user (localhost) and password "mypass"
  read_mail:
    host: imap.myhost.com
    password: mypass

- name: Read mails from a server with no TLS on port 42
  read_mail:
    host: imap.myhost.com
    port: 42
    username: myuser
    password: mypass
    tls: no

- name: Read mails with subject "mysubject", and to "example@example.com"
  read_mail:
    host: imap.myhost.com
    port: 42
    username: myuser
    password: mypass
    filter:
      subject: mysubject
      to: example@example.com

- name: Read unseen mails with 'subject' filter
  read_mail:
    host: imap.myhost.com
    username: myuser
    password: mypass
    filter:
      subject: mysubject
      unseen:
'''

RETURN = r'''
host:
    description: The host used to perform the request
    type: str
    returned: always
username:
    description: The username used to perform the request
    type: str
    returned: always
mails:
    description: A list of dictionaries with the keys 'to', 'from', 'subject' and 'body',
        where each one represents an email that satisfied the filter
    type: list
    returned: always
mails_count:
    description: The email count that satisfied the filter
    type: int
    returned: always
'''
import imaplib

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import PY3

if PY3:
    from email.header import decode_header
    from email import message_from_bytes as message_parser
else:
    from email.Header import decode_header
    from email import message_from_string as message_parser


def run_module():
    module_args = dict(
        host=dict(type='str', required=False, default='localhost'),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        tls=dict(type='bool', required=False, default=True),
        port=dict(type='int', required=False, default=-1),
        mailbox=dict(type='str', required=False, default='INBOX'),
        filter=dict(type='dict', required=False, default={'ALL': ''})
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=True,
        username=module.params['username'],
        host=module.params['host'],
        mails=[],
        mails_count=0
    )

    if module.check_mode:
        module.exit_json(**result)

    # create connection
    try:
        if module.params['tls']:
            port = 993 if module.params['port'] < 0 else module.params['port']
            M = imaplib.IMAP4_SSL(module.params['host'], port=port)
        else:
            port = 143 if module.params['port'] < 0 else module.params['port']
            M = imaplib.IMAP4(module.params['host'], port=port)
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    # login
    try:
        M.login(module.params['username'], module.params['password'])
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    # selects mailbox
    M.select(module.params['mailbox'])

    # makes the filter
    search_array = []
    for k, v in module.params['filter'].items():
        search_array.append(k)
        if v:
            search_array.append(v)
    status, search = M.search(None, *search_array)
    if status != 'OK':
        module.fail_json(msg='Error filtering', **result)

    # build result mails
    for email_id in search[0].split():
        status, content = M.fetch(email_id, '(RFC822)')
        if status != 'OK':
            module.fail_json(msg='Error parsing', **result)

        msg = message_parser(content[0][1])

        result['mails'].append({
            'to': decode_header(msg['to'])[0][0],
            'from': decode_header(msg['from'])[0][0],
            'subject': decode_header(msg['subject'])[0][0],
            'body': msg.get_payload(0).get_payload(None, True)
        })
    result['mails_count'] = len(result['mails'])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()