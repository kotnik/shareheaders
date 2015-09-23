import re
import os
import fnmatch
import codecs
import email.parser
import email.utils
import ipaddress


def load_mail_file(filename):
    with codecs.open(filename, "r", encoding="utf-8", errors="ignore") as mail_file:
        return email.parser.Parser().parse(mail_file)


def mails(mails_dir):
    for path, dirs, files in os.walk(os.path.abspath(mails_dir)):
        for filename in fnmatch.filter(files, "*"):
            yield load_mail_file(os.path.join(path, filename))


def extract_mail_adresses(text):
    for mail in re.findall(r'[\w\.-]+@[\w\.-]+', text):
        yield mail


def extract_ips(text):
    for ip in re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text):
        yield ip


def ip_private(ip):
    private = False
    if ip == "127.0.0.1":
        return True
    for net in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(net):
            private = True
    return private


def parse_date(dt):
    return email.utils.parsedate(dt)
