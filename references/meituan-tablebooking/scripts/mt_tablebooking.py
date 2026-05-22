#!/usr/bin/env python3
"""
美团/大众点评订座 CLI - 麦家小馆草稿版

保留真实 Passport 授权流程形态；订座 endpoint 未配置时，不向 placeholder
endpoint 发起 HTTP 请求。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get(
    "MT_TABLEBOOKING_BASE_URL",
    "https://m.dianping.com/tablebooking/mdp/ajax/",
)
ENDPOINT_INDEX = os.environ.get("MT_TABLEBOOKING_ENDPOINT_INDEX", "<BOOKING_INDEX_ENDPOINT_PLACEHOLDER>")
ENDPOINT_BOOK = os.environ.get("MT_TABLEBOOKING_ENDPOINT_BOOK", "<BOOK_TABLE_ENDPOINT_PLACEHOLDER>")
ENDPOINT_DETAIL = os.environ.get("MT_TABLEBOOKING_ENDPOINT_DETAIL", "<BOOKING_DETAIL_ENDPOINT_PLACEHOLDER>")
ENDPOINT_CANCEL = os.environ.get("MT_TABLEBOOKING_ENDPOINT_CANCEL", "<BOOKING_CANCEL_ENDPOINT_PLACEHOLDER>")
DEFAULT_CLIENT_ID = "<MEITUAN_TABLEBOOKING_CLIENT_ID_PLACEHOLDER>"
ENV_TOKEN_KEY = "MT_TABLEBOOKING_TOKEN"
TIMEOUT = 30


class TableBookingError(Exception):
    """订座流程错误。"""


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    return "PLACEHOLDER" in value or value.startswith("<")


def _skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _passport_dir() -> Path:
    return _skill_dir() / "references" / "meituan-passport-user-auth"


def _run(cmd: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _ensure_passport_cli() -> None:
    if shutil.which("pt-passport"):
        return

    install_script = _passport_dir() / "scripts" / "install.sh"
    if not install_script.exists():
        raise TableBookingError("未找到 meituan-passport-user-auth 安装脚本，无法触发授权。")

    result = _run(["bash", str(install_script)], timeout=120)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise TableBookingError(f"pt-passport 安装失败：{detail[:500]}")


def _extract_token(output: str) -> str | None:
    text = output.strip()
    if not text:
        return None
    for line in text.splitlines():
        if line.startswith("Token:"):
            return line.split("Token:", 1)[1].strip()
    if "\n" not in text and not text.startswith("AUTH_LINK:"):
        return text
    return None


def _auto_auth(client_id: str, env: str) -> str:
    if _is_placeholder(client_id):
        raise TableBookingError(
            "美团订座 client_id 仍为 placeholder。请先配置 MT_TABLEBOOKING_CLIENT_ID，"
            "再触发真实 Passport 授权。"
        )

    _ensure_passport_cli()

    env_args = [] if env == "prod" else ["--env", env]

    cached = _run(["pt-passport", "get-token", "--client_id", client_id, *env_args], timeout=10)
    if cached.returncode == 0:
        token = _extract_token(cached.stdout)
        if token:
            return token

    get_code = _run(["pt-passport", "auth", "get-code", "--client_id", client_id, *env_args], timeout=30)
    if get_code.returncode != 0:
        detail = (get_code.stderr or get_code.stdout).strip()
        raise TableBookingError(f"授权链接获取失败：{detail[:500]}")

    token = _extract_token(get_code.stdout)
    if token:
        return token

    auth_link = None
    for line in get_code.stdout.splitlines():
        if line.startswith("AUTH_LINK:"):
            auth_link = line.split("AUTH_LINK:", 1)[1].strip()
            break

    if auth_link:
        print("请用美团 App 打开以下链接完成授权：")
        print(auth_link)
        print("等待授权中...", file=sys.stderr)

    poll = _run(["pt-passport", "auth", "poll-token", "--client_id", client_id], timeout=600)
    if poll.returncode != 0:
        detail = (poll.stderr or poll.stdout).strip()
        raise TableBookingError(f"授权失败：{detail[:500]}")

    token = _extract_token(poll.stdout)
    if not token:
        final = _run(["pt-passport", "get-token", "--client_id", client_id, *env_args], timeout=10)
        token = _extract_token(final.stdout)

    if not token:
        raise TableBookingError("授权完成但未获取到 token。")
    return token


def _endpoint_url(endpoint: str) -> str:
    return BASE_URL.rstrip("/") + "/" + endpoint.lstrip("/")


def _request(token: str, endpoint: str, params: dict[str, object] | None = None, method: str = "GET") -> dict:
    if _is_placeholder(endpoint):
        raise TableBookingError("订座接口尚未配置，当前不会向 placeholder endpoint 发起 HTTP 请求。")

    headers = {
        "User-Agent": "MeituanTableBooking-Skill/0.1",
        "Accept": "application/json",
        "token": token,
    }
    url = _endpoint_url(endpoint)
    body = None
    if method == "GET" and params:
        url += "?" + urllib.parse.urlencode(params)
    elif params:
        body = urllib.parse.urlencode(params).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        raise TableBookingError(f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise TableBookingError(f"网络异常：{exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise TableBookingError("服务端返回非 JSON 响应。") from exc


def _placeholder_message(action: str, shop_id: str) -> str:
    return (
        f"【麦家小馆订座】{action}\n"
        f"门店 shop_id：{shop_id}\n"
        "状态：订座接口尚未配置。\n"
        "已保留 Passport 授权流程；配置真实 booking endpoint 后，此命令将执行对应接口请求。"
    )


def cmd_index(token: str, shop_id: str, date: str | None) -> str:
    try:
        resp = _request(token, ENDPOINT_INDEX, {"dpShopId": shop_id, "date": date or ""})
    except TableBookingError as exc:
        if "placeholder endpoint" in str(exc):
            return _placeholder_message("查询可订信息", shop_id)
        raise
    return json.dumps(resp, ensure_ascii=False, indent=2)


def cmd_book_table(
    token: str,
    shop_id: str,
    people_count: int,
    date: str,
    time: str,
    table_type_id: str | None,
) -> str:
    params: dict[str, object] = {
        "dpShopId": shop_id,
        "peopleCount": people_count,
        "date": date,
        "time": time,
    }
    if table_type_id:
        params["tableTypeId"] = table_type_id
    try:
        resp = _request(token, ENDPOINT_BOOK, params, method="POST")
    except TableBookingError as exc:
        if "placeholder endpoint" in str(exc):
            return (
                _placeholder_message("创建预订", shop_id)
                + f"\n预订参数：{people_count}人，{date} {time}"
                + (f"，桌型 {table_type_id}" if table_type_id else "")
            )
        raise
    return json.dumps(resp, ensure_ascii=False, indent=2)


def cmd_booking_detail(token: str, shop_id: str) -> str:
    try:
        resp = _request(token, ENDPOINT_DETAIL, {"dpShopId": shop_id})
    except TableBookingError as exc:
        if "placeholder endpoint" in str(exc):
            return _placeholder_message("查询预订", shop_id)
        raise
    return json.dumps(resp, ensure_ascii=False, indent=2)


def cmd_booking_cancel(token: str, shop_id: str) -> str:
    try:
        resp = _request(token, ENDPOINT_CANCEL, {"dpShopId": shop_id}, method="POST")
    except TableBookingError as exc:
        if "placeholder endpoint" in str(exc):
            return _placeholder_message("取消预订", shop_id)
        raise
    return json.dumps(resp, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="美团/大众点评订座 — 查可订信息、创建预订、查预订、取消预订",
    )
    parser.add_argument(
        "action",
        choices=["index", "book_table", "booking_detail", "booking_cancel"],
        help="操作类型",
    )
    parser.add_argument("shop_id", help="点评门店 ID")
    parser.add_argument("--token", default=None, help="登录 token，可用环境变量 MT_TABLEBOOKING_TOKEN 代替")
    parser.add_argument("--client-id", default=os.environ.get("MT_TABLEBOOKING_CLIENT_ID", DEFAULT_CLIENT_ID))
    parser.add_argument("--env", default=os.environ.get("MT_TABLEBOOKING_ENV", "prod"), choices=["prod", "test"])
    parser.add_argument("--people-count", type=int, help="就餐人数（book_table 必填）")
    parser.add_argument("--date", help="日期 YYYY-MM-DD（index 可选，book_table 必填）")
    parser.add_argument("--time", help="时间 HH:mm（book_table 必填）")
    parser.add_argument("--table-type-id", help="桌型 ID（从 index 返回结果获取，可选）")

    args = parser.parse_args()

    try:
        token = args.token or os.environ.get(ENV_TOKEN_KEY) or _auto_auth(args.client_id, args.env)

        if args.action == "index":
            result = cmd_index(token, args.shop_id, args.date)
        elif args.action == "book_table":
            if args.people_count is None or not args.date or not args.time:
                parser.error("book_table requires --people-count, --date and --time")
            result = cmd_book_table(token, args.shop_id, args.people_count, args.date, args.time, args.table_type_id)
        elif args.action == "booking_detail":
            result = cmd_booking_detail(token, args.shop_id)
        else:
            result = cmd_booking_cancel(token, args.shop_id)

        print(result)
        return 0
    except TableBookingError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("已取消。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
