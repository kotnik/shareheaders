#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
from urllib.request import urlopen
from contextlib import closing
import time
import pickle
import signal

sys.path.append(os.getcwd())
import utils


MD = "./Headers"
FREEGEOIP = "http://freegeoip.net/json/"
DELAY = 0.36
DB_BACKUP = "/home/kotnik/tmp/brisati/ip.pkl"


def totals():
    """ Ukupni brojevi.
    """
    all_mails = {"to": set(), "from": set()}

    for msg in utils.mails(MD):
        if "to" in msg:
            for mail in utils.extract_mail_adresses(msg["to"]):
                all_mails["to"].add(mail)
        if "from" in msg:
            for mail in utils.extract_mail_adresses(msg["from"]):
                all_mails["from"].add(mail)

    print("Total from:", len(all_mails["from"]), "Total to:", len(all_mails["to"]))


def mail_ip_location():
    """ Tabela mejl, ip, lokacija, vreme.
    """
    lookup_map = dict()
    if os.path.exists(DB_BACKUP):
        with open(DB_BACKUP, "rb") as f:
            lookup_map = pickle.load(f)

    # Sačuvaj IP lookup cache u slučaju prekida programa.
    def signal_handler(signal, frame):
            print("interuppted...")
            with open(DB_BACKUP, "wb") as f:
                pickle.dump(lookup_map, f, pickle.HIGHEST_PROTOCOL)
            sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler)

    print("From\tIP\tCountry\tCity\tDatetime\tDate\tTime\tMailer")
    for msg in utils.mails(MD):

        if not "from" in msg or "From" not in msg:
            continue

        received = msg.get_all("received")
        if not received:
            received = msg.get_all("Received")

        if received:
            # Uzimamo poslednji `received` heder, u njemu se nalazi IP adresa
            # pošiljaoca.
            first_bounce = received[-1]
            try:
                fr = next(utils.extract_mail_adresses(msg["From"]))
            except StopIteration:
                fr = None
            try:
                if not fr:
                    fr = next(utils.extract_mail_adresses(msg["from"]))
                ip = next(utils.extract_ips(first_bounce))
            except StopIteration:
                continue
            if utils.ip_private(ip):
                continue

            if ip not in lookup_map:
                url = FREEGEOIP + ip
                with closing(urlopen(url)) as response:
                    location = json.loads(response.read().decode())
                    location_city = location["city"]
                    location_country = location["country_name"]
                lookup_map[ip] = {
                    "country": location_country,
                    "city": location_city,
                }
                # Freegeoip dozvoljava 10k upita po satu.
                time.sleep(DELAY)

            # Ovo nije keširano jer je dodato kasnije. Posle slobodno može ići
            # u blok iznad.
            msg_datetime = msg.get("date", "")
            msg_date, msg_time = ("", "")
            if msg_datetime:
                parsed_datetime = utils.parse_date(msg_datetime)
                if parsed_datetime:
                    msg_date = time.strftime("%d %b %Y", parsed_datetime)
                    msg_time = time.strftime("%H:%M:%S", parsed_datetime)
            lookup_map[ip]["datetime"] = msg_datetime
            lookup_map[ip]["date"] = msg_date
            lookup_map[ip]["time"] = msg_time

            # Program korišten za slanje mejla.
            msg_mailer = msg.get("X-Mailer", "")
            lookup_map[ip]["mailer"] = msg_mailer

            # Štampaj!
            print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                fr.lower(),
                ip,
                lookup_map[ip]["country"],
                lookup_map[ip]["city"],
                lookup_map[ip]["datetime"],
                lookup_map[ip]["date"],
                lookup_map[ip]["time"],
                lookup_map[ip]["mailer"],
            ))

    # Sačuvaj IP lookup cache.
    with open(DB_BACKUP, "wb") as f:
        pickle.dump(lookup_map, f, pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    # totals()

    mail_ip_location()
