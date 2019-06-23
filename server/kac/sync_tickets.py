import requests


def main():
    page_id = 1
    page_size = 100

    while True:
        resp = requests.get(f'https://store.uburners.com/tc-api/67EB12E9/tickets_info/{page_size}/{page_id}/').json()

        for t in resp[:-1]:
            #print(t['data']['checksum'])
            print("INSERT INTO ticket(event_id, code) VALUES ('2019_precomp', '{}') ON CONFLICT DO NOTHING;".format(t['data']['checksum']))
        if resp[-1]['additional']['results_count'] < page_size:
            break
        page_id += 1


if __name__ == '__main__':
    main()



    # event_id varchar(200) REFERENCES event(id),
    # code text,
