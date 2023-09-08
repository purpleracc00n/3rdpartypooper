# 3rdpartypooper

 It uses a combination of DNS lookups and HTTP requests to determine the existence of a tenancy on third parties.

 To run, simply do:

```
$ python3 3rdpartypooper.py <keyword> 
```

Where <keyword> is the object of the search and you should best think about it as the most representative name possible for the company you are looking for.
Examples:
- microsoft
- google
- apple
- etc.

## How does it work?

It uses basic enumeration principles and a built-in list of third parties which are known to create customer tenancies as follows: <customer_name>.<thirdparty_root_domain>.

Then, performs the following checks:
* DNS lookups of the target subdomain versus a random one
* Checks the HTTPS accessibility of the target subdomain vs a random one
* Checks status codes of the target subdomain vs a random one
* Checks Location header of the redirects (target subdomain vs a random one)
* Checks the Content-Length header of the pages (target subdomain vs a random one)
* Follows redirections and spots differences in the HTML (target subdomain vs a random one)
* Follows redirections, renders the page with requests_html and spots differences in the HTML (target subdomain vs a random one)
* Uses undetected_chromedriver to open the subdomains in Chrome and check for differences in HTML

Work in progress so if you spot bugs let me know!
Also, if you want to help me improve the built-in wordlist of thrid parties drop me a message.

## Caveats

Requires Google Chrome.

Make sure undetected-chromedriver and google chrome are in compatible (latest) versions... Sometimes after not using the tool for a while you may find that the Chrome version is ahead of undetected-chromedriver, just do:
```
$ pip3 install --upgrade undetected-chromedriver
```

