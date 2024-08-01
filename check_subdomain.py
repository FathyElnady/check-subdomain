import requests
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_subdomains(domain):
    url = "https://crt.sh/?q=%25.{}&output=json".format(domain)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return set(entry['name_value'] for entry in response.json())

def check_subdomain(subdomain):
    try:
        response = requests.get("http://{}".format(subdomain))
        return subdomain, response.status_code == 200
    except requests.RequestException:
        return subdomain, False

def save_output(subdomains, output_file, output_type):
    if output_type == 'json':
        with open(output_file, 'w') as f:
            json.dump(subdomains, f, indent=4)
    elif output_type == 'txt':
        with open(output_file, 'w') as f:
            for subdomain in subdomains:
                f.write("{}\n".format(subdomain))
    elif output_type == 'html':
        with open(output_file, 'w') as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n<title>Subdomains</title>\n</head>\n<body>\n")
            f.write("<h1>Subdomains for domain</h1>\n")
            f.write("<ul>\n")
            for subdomain in subdomains:
                f.write('<li><a href="http://{}" target="_blank">{}</a></li>\n'.format(subdomain, subdomain))
            f.write("</ul>\n</body>\n</html>")

def main():
    parser = argparse.ArgumentParser(description='Fetch and check subdomains.')
    parser.add_argument('-u', '--url', required=True, help='The domain name to check.')
    parser.add_argument('-l', '--limit', type=int, default=None, help='Number of subdomains to fetch and check (default: all).')
    parser.add_argument('--json', action='store_true', help='Save output as JSON.')
    parser.add_argument('--txt', action='store_true', help='Save output as TXT.')
    parser.add_argument('--html', action='store_true', help='Save output as HTML.')

    args = parser.parse_args()

    if not args.json and not args.txt and not args.html:
        args.json = True  # Default to JSON if no format is specified

    domain = args.url
    limit = args.limit
    print("Fetching subdomains for {}...".format(domain))
    
    subdomains = get_subdomains(domain)
    
    if limit:
        subdomains = list(subdomains)[:limit]  # Limit the number of subdomains to fetch

    # Use a sorted list to ensure consistent order
    unique_subdomains = sorted(set(subdomains))

    valid_subdomains = set()  # To store only the valid subdomains
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_subdomain = {executor.submit(check_subdomain, sub): sub for sub in unique_subdomains}
        for future in as_completed(future_to_subdomain):
            subdomain, is_valid = future.result()
            if is_valid:
                valid_subdomains.add(subdomain)
    
    # Prepare the output file name
    if args.json:
        output_file = "ssl-tool-{}.json".format(domain)
    elif args.txt:
        output_file = "ssl-tool-{}.txt".format(domain)
    elif args.html:
        output_file = "ssl-tool-{}.html".format(domain)
    
    # Save or print the results
    if args.json:
        save_output(list(valid_subdomains), output_file, 'json')
        print("Output saved to {}".format(output_file))
    
    if args.txt:
        save_output(list(valid_subdomains), output_file, 'txt')
        print("Output saved to {}".format(output_file))
    
    if args.html:
        save_output(list(valid_subdomains), output_file, 'html')
        print("Output saved to {}".format(output_file))

if __name__ == "__main__":
    main()
