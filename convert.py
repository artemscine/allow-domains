#!/usr/bin/python3.10

import tldextract
from pathlib import Path
import json
import os
import subprocess

rusDomainsInsideCategories='Categories'
rusDomainsInsideServices='Services'
DiscordSubnets = 'Subnets/IPv4/discord.lst'
MetaSubnets = 'Subnets/IPv4/meta.lst'
TwitterSubnets = 'Subnets/IPv4/twitter.lst'
TelegramSubnets = 'Subnets/IPv4/telegram.lst'

def domains_from_file(filepath):
    domains = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                domain = line.strip()
                if domain:
                    domains.append(domain)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    return domains

def generate_srs_domains(domains, output_name):
    output_directory = 'JSON'
    compiled_output_directory = 'SRS'

    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(compiled_output_directory, exist_ok=True)

    data = {
        "version": 3,
        "rules": [
            {"domain_suffix": domains}
        ]
    }

    json_file_path = os.path.join(output_directory, f"{output_name}.json")
    srs_file_path = os.path.join(compiled_output_directory, f"{output_name}.srs")

    try:
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"JSON file generated: {json_file_path}")

        subprocess.run(
            ["sing-box", "rule-set", "compile", json_file_path, "-o", srs_file_path], check=True
        )
        print(f"Compiled .srs file: {srs_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Compile error {json_file_path}: {e}")
    except Exception as e:
        print(f"Error while processing {output_name}: {e}")

def generate_srs_for_categories(directories, output_json_directory='JSON', compiled_output_directory='SRS'):
    os.makedirs(output_json_directory, exist_ok=True)
    os.makedirs(compiled_output_directory, exist_ok=True)

    exclude = {"meta", "twitter", "discord"}

    for directory in directories:
        for filename in os.listdir(directory):
            if any(keyword in filename for keyword in exclude):
                continue
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                domains = []
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        domain = line.strip()
                        if domain:
                            domains.append(domain)

            data = {
                "version": 3,
                "rules": [
                    {
                        "domain_suffix": domains
                    }
                ]
            }

            output_file_path = os.path.join(output_json_directory, f"{os.path.splitext(filename)[0]}.json")

            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                json.dump(data, output_file, indent=4)

            print(f"JSON file generated: {output_file_path}")

    print("\nCompile JSON files to .srs files...")
    for filename in os.listdir(output_json_directory):
        if filename.endswith('.json'):
            json_file_path = os.path.join(output_json_directory, filename)
            srs_file_path = os.path.join(compiled_output_directory, f"{os.path.splitext(filename)[0]}.srs")
            try:
                subprocess.run(
                    ["sing-box", "rule-set", "compile", json_file_path, "-o", srs_file_path], check=True
                )
                print(f"Compiled .srs file: {srs_file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Compile error {json_file_path}: {e}")

def generate_srs_combined(input_subnets_file, input_domains_file, output_json_directory='JSON', compiled_output_directory='SRS'):
    os.makedirs(output_json_directory, exist_ok=True)
    os.makedirs(compiled_output_directory, exist_ok=True)

    domains = []
    if os.path.exists(input_domains_file):
        with open(input_domains_file, 'r', encoding='utf-8') as file:
            domains = [line.strip() for line in file if line.strip()]

    subnets = []
    if os.path.exists(input_subnets_file):
        with open(input_subnets_file, 'r', encoding='utf-8') as file:
            subnets = [line.strip() for line in file if line.strip()]

    if input_subnets_file == "Subnets/IPv4/discord.lst":
        data = {
            "version": 3,
            "rules": [
                {
                    "domain_suffix": domains
                },
                {
                    "network": ["udp"],
                    "ip_cidr": subnets,
                    "port_range": ["50000:65535"]
                }
            ]
        }
    else:
        data = {
            "version": 3,
            "rules": [
                {
                    "domain_suffix": domains,
                    "ip_cidr": subnets
                }
            ]
        }

    filename = os.path.splitext(os.path.basename(input_subnets_file))[0]
    output_file_path = os.path.join(output_json_directory, f"{filename}.json")

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(data, output_file, indent=4)

    print(f"JSON file generated: {output_file_path}")

    srs_file_path = os.path.join(compiled_output_directory, f"{filename}.srs")
    try:
        subprocess.run(
            ["sing-box", "rule-set", "compile", output_file_path, "-o", srs_file_path], check=True
        )
        print(f"Compiled .srs file: {srs_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Compile error {output_file_path}: {e}")

if __name__ == '__main__':
    # Sing-box ruleset main
    russia_inside = domains_from_file('Russia/inside-raw.lst')
    russia_outside = domains_from_file('Russia/outside-raw.lst')
    ukraine_inside = domains_from_file('Ukraine/inside-raw.lst')
    generate_srs_domains(russia_inside, 'russia_inside')
    generate_srs_domains(russia_outside, 'russia_outside')
    generate_srs_domains(ukraine_inside, 'ukraine_inside')

    # Sing-box categories
    directories = ['Categories', 'Services']
    generate_srs_for_categories(directories)

    # Sing-box subnets + domains
    generate_srs_combined(DiscordSubnets, "Services/discord.lst")
    generate_srs_combined(TwitterSubnets, "Services/twitter.lst")
    generate_srs_combined(MetaSubnets, "Services/meta.lst")
    generate_srs_combined(TelegramSubnets, "Services/telegram.lst")
