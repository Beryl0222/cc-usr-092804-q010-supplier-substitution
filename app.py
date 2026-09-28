"""moon_cake 命令行入口。"""
import argparse, json, sqlite3
from pathlib import Path
from moon_cake.workflow import Workflow

def main(argv=None):
    parser = argparse.ArgumentParser(description='本地业务状态服务')
    parser.add_argument('--db', default='service.sqlite3')
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('apply'); create.add_argument('key'); create.add_argument('subject'); create.add_argument('state'); create.add_argument('--actor', required=True); create.add_argument('--request', required=True); create.add_argument('--payload', default='{}'); create.add_argument('--effective', default='2026-09-28T00:00:00+00:00')
    show = sub.add_parser('show'); show.add_argument('key')
    sub.add_parser('summary')
    args = parser.parse_args(argv)
    db = sqlite3.connect(args.db)
    service = Workflow(db)
    if args.command == 'apply':
        value = service.apply(args.key, args.subject, args.state, json.loads(args.payload), args.actor, args.request, args.effective)
        print(json.dumps(value, ensure_ascii=False, default=lambda x: x.__dict__))
    elif args.command == 'show':
        print(json.dumps(service.show(args.key), ensure_ascii=False, default=lambda x: x.__dict__))
    else:
        print(json.dumps(service.summary(), ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
