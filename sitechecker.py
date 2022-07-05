import argparse, sys, pathlib, asyncio
from http.client import HTTPConnection
from urllib.parse import urlparse
import aiohttp

def read_user_cli_args():
    parser = argparse.ArgumentParser(
        prog = 'sitechecker', description = 'check the availability of websites'
    )
    parser.add_argument(
        '-u',
        '--urls',
        metavar='URLs',
        nargs = '+',
        type = str,
        default= [],
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
        action= 'store_true',
        help= 'run the connectivity check asynchronously',
    )
    return parser.parse_args(input('Enter Argument(-u, -f, -a), site: ').split(' '))

def display_check_result(result, url, error=''):
    print(f'The status of "{url}" is: ', end='')
    if result:
        print('Online!')
    else:
        print(f'"Offline?"\n Error: "{error}"')

def _get_websites_urls(user_args):
    urls = user_args.urls
    if user_args.input_file:
        urls += _read_urls_from_file(user_args.input_file)
    return urls

def _read_urls_from_file(file):
    file_path = pathlib.Path(file)
    if file_path.is_file():
        with file_path.open() as urls_file:
            urls = [url.strip() for url in urls_file]
            if urls:
                return urls 
            print(f'Error: empty input file', "{file}", file = sys.stderr)
    else:
        print('Error: input file not found', file = sys.stderr)
    return []
def site_is_online(url, timeout=2):
    error = Exception('unknown error')
    parser = urlparse(url)
    host = parser.netloc or parser.path.split('/')[0]
    for port in (80, 443):
        connection = HTTPConnection(host=host, port=port, timeout= timeout)
        try:
            connection.request('HEAD', '/')
            return True
        except Exception as e:
            error = e
        finally:
            connection.close()
    raise error

async def site_is_online_async(url, timeout=2):
    error= Exception('unknown error')
    parser = urlparser(url)
    host = parser.netloc or parser.path.split('/')[0]
    for scheme in ('http', 'https'):
        target_url = scheme + '://'+ host
        async with aiohttp.ClientSession() as session:
            try:
                await session.head(target_url, timeout=timeout)
                return True
            except asyncio.exceptions.TimeoutError:
                error = Exception('timed out')
            except Exception as e:
                error = e
    raise error

async def _asynchronous_check(urls):
    async def _check(url):
        error = ''
        try:
            result = await site_is_online_async(url)
        except Exception as e:
            result = False
            error = str(e)
        display_check_result(result, url, error)
    await asyncio.gather(*(_check(url)for url in urls))

def _synchronous_check(urls):
    for url in urls:
        error = ''
        try:
            result = site_is_online(url)
        except Exception as e:
            result = False 
            error = str(e)
        display_check_result(result, url, error)

def main():
    user_args = read_user_cli_args()
    urls = _get_websites_urls(user_args)
    if not urls:
        print('Error: no URLs to check', file = sys.stderr)
        sys.exit(1)
    if user_args.asynchronous:
        asyncio.run(_asynchronous_check(urls))
    else:
        _synchronous_check(urls)

if __name__=='__main__':
    main()