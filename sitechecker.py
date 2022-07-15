import argparse, sys, pathlib, asyncio
from http.client import HTTPConnection #this to establish connection with the target url
from urllib.parse import urlparse #to parse the target urls
import aiohttp #third party libary that permit asynchronously HTTP requests

def read_user_cli_args():
    parser = argparse.ArgumentParser(
        prog = 'sitechecker', description = 'check the availability of websites'
    )
    parser.add_argument(
        '-u',
        '--urls',
        metavar='URLs',#set name for argument in usage
        nargs = '+',#tells argparse to accept a list of command line arg after the metavar switch
        type = str,#set the data type to string
        default= [],#set the command line arg to an empty list by default
        help = 'enter one or more website URls',
    )
    parser.add_argument(
        '-f',
        '--input_file',
        metavar='FILE',
        type= str,
        default='',
        help='read URLs from a file',
    )
    parser.add_argument(
        '-a',
        '--asynchronous',
        action= 'store_true', #tells argsparse that -a andd --asynchronous are Boolean flags that store True
        help= 'run the connectivity check asynchronously',
    )
    return parser.parse_args(input('Enter Argument(-u, -f, -a), site: ').split(' ')) #to avoid error

#defining function that interract with the user
def display_check_result(result, url, error=''):
    print(f'The status of "{url}" is: ', end='')
    if result:
        print('Online!')
    else:
        print(f'"Offline?"\n Error: "{error}"')

#function that read urls from the args
def _get_websites_urls(user_args):
    urls = user_args.urls
    if user_args.input_file: #allow file to be inputed in the args
        urls += _read_urls_from_file(user_args.input_file)
    return urls

#function that permit reading URLs from file
def _read_urls_from_file(file):
    file_path = pathlib.Path(file) #changing the file argument into a pathlib.Path object
    if file_path.is_file(): #checking if file inputed is file in the local system
        with file_path.open() as urls_file: #opening the file path
            urls = [url.strip() for url in urls_file] #removing any whitespace from every line in the file to prevent processsing errors later
            if urls: #nested conditional to check if any URL has been gathered
                return urls #return the resulting list of URLs from the file
            print(f'Error: empty input file', "{file}", file = sys.stderr) #if no URL has been gathered.
    else:
        print('Error: input file not found', file = sys.stderr)
    return [] #empty list if no valid URLs
def site_is_online(url, timeout=2):
    #return true if the target URL is online, raise an exception otherwise.
    error = Exception('unknown error')
    parser = urlparse(url)
    host = parser.netloc or parser.path.split('/')[0] #extracting host name from the target URL
    for port in (80, 443): #HTTP and HTTPS ports
        connection = HTTPConnection(host=host, port=port, timeout= timeout)
        try: #attempting to make HEAD request
            connection.request('HEAD', '/')
            return True
        except Exception as e:
            error = e
        finally:
            connection.close()
    raise error #raises the exception stored in error if the loop finishes without a successful request.

#asynchronously cheking whether site is online
async def site_is_online_async(url, timeout=2): #return true if online otherwise raise an exception
    error= Exception('unknown error') #exception instance
    parser = urlparse(url)
    host = parser.netloc or parser.path.split('/')[0] # using or operator to extract the host name from the target URLs
    for scheme in ('http', 'https'): #checking website availability on either http and https
        target_url = scheme + '://'+ host #build a url using scheme and host
        async with aiohttp.ClientSession() as session: #async with statement to handle aiohttp.ClientSession
            try:
                await session.head(target_url, timeout=timeout) #await HEAD request on target url
                return True
            except asyncio.exceptions.TimeoutError: #updating the exception
                error = Exception('timed out')
            except Exception as e:
                error = e
    raise error #raises the exception stored in error if the loop finishes without a successful requests

async def _asynchronous_check(urls):
    async def _check(url): #defines an inner async function _check(). permit reuse check of single url for connectivity
        error = ''
        try:
            result = await site_is_online_async(url) #True or False will be stored in error depending on the availability of the website.
        except Exception as e:
            result = False
            error = str(e)
        display_check_result(result, url, error) #display information about website's availability
    await asyncio.gather(*(_check(url)for url in urls)) #runs a list of awaitable objects concurrently and returns an agregated list of resulting values i all awaitable objects complete successfully.
#calling check for each URL

def _synchronous_check(urls):
    for url in urls: #for loop to iterate over target URLs
        error = '' #error which will hold the message that will be displayed if the script does not get a response from the target website.
        try: #trying to catch any exception that might occour in the calling of site_is_online on the target URLs
            result = site_is_online(url)
        except Exception as e:
            result = False 
            error = str(e)
        display_check_result(result, url, error)

def main():
    user_args = read_user_cli_args()
    urls = _get_websites_urls(user_args)
    if not urls: #if user passes invalid URLs
        print('Error: no URLs to check', file = sys.stderr)
        sys.exit(1)
    if user_args.asynchronous: #if user passes argument -a
        asyncio.run(_asynchronous_check(urls))
    else:
        _synchronous_check(urls)
#conditional statement to run the script
if __name__=='__main__':
    main()