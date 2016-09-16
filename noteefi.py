import time
import requests
import json
import websocket
from websocket import create_connection
import pymongo
from pymongo import MongoClient

telegram_token = "BOTS_TELEGRAM_TOKEN_ID_HERE"
mon_pending = []
sub_pending = []
unmon_pending = []
unsub_pending = []
tpslist = []


def telegram(method, params=None):
    url = "https://api.telegram.org/bot"+telegram_token+"/"
    params = params
    r = requests.get(url+method, params = params).json()
    return r

def ck(chat_id):
    custom_keyboard = []
    if chat_id in monitor_list:
        if len(monitor_list[chat_id]) < 20:
            custom_keyboard.append(["/monitor_account"])
    if chat_id in subscribe_list:
        if len(subscribe_list[chat_id]) < 20:
            custom_keyboard.append(["/subscribe_category"])
    if chat_id in monitor_list:
        if len(monitor_list[chat_id]) > 0:
            custom_keyboard.append(["/monitoring_list", "/cancel_monitoring"])
    if chat_id in subscribe_list:
        if len(subscribe_list[chat_id]) > 0:
            custom_keyboard.append(["/subscription_list", "/cancel_subscription"])
    return custom_keyboard

def db_gen():
    mon = {}
    sub = {}
    mlist = {}
    slist = {}
    for r in coll_monid.find():
        if r["id"] in mon.keys():
            mon[r["id"]].append(r["tgid"])
        else:
            mon[r["id"]] = [r["tgid"]]
    for r in coll_subid.find():
        if r["id"] in sub.keys():
            sub[r["id"]].append(r["tgid"])
        else:
            sub[r["id"]] = [r["tgid"]]
    for r in coll_monid.find():
        if r["tgid"] in mlist.keys():
            mlist[r["tgid"]].append(r["id"])
        else:
            mlist[r["tgid"]] = [r["id"]]
    for r in coll_subid.find():
        if r["tgid"] in slist.keys():
            slist[r["tgid"]].append(r["id"])
        else:
            slist[r["tgid"]] = [r["id"]]
    return (mon, sub, mlist, slist)

def update_db(last):
    updates = telegram("getUpdates", {"offset":last+1, "limit": 100})["result"]
    if updates == "":
        return last
    for i in range(len(updates)):
        chat_id = updates[i]["message"]["from"]["id"]
        update_id = updates[i]["update_id"]
        try:
            cmd = updates[i]["message"]["text"]
        except:
            cmd = ""
        if update_id > last and cmd != "":
            if cmd.lower() == "/help":
                msg = "List of commands\n\n/monitor_account\n/subscribe_category\n/monitoring_list\n/cancel_monitoring\n/subscription_list\n/cancel_subscription"
                m = telegram("sendMessage", {"chat_id":chat_id, "text":msg})
            elif cmd == "/monitor_account":
                try:
                    if len(monitor_list[chat_id]) >= 20:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You have reached maximum number of monitoring"})
                    else:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter account to monitor"})
                        mon_pending.append(chat_id)
                except:
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter account to monitor"})
                    mon_pending.append(chat_id)
            elif cmd == "/subscribe_category":
                try:
                    if len(subscribe_list[chat_id]) >= 20:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You have reached maximum number of subscription"})
                    else:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter category to subscribe"})
                        sub_pending.append(chat_id)
                except:
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter category to subscribe"})
                    sub_pending.append(chat_id)
            elif cmd == "/monitoring_list":
                list = ""
                if chat_id in monitor_list:
                    monitor_list[chat_id].sort()
                    for i in monitor_list[chat_id]:
                        list += i+"\n"
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Your monitoring list:\n" + list})
                else:
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are not monitoring"})
            elif cmd == "/cancel_monitoring":
                custom_keyboard = []
                if chat_id in monitor_list:
                    monitor_list[chat_id].sort()
                    for c in monitor_list[chat_id]:
                        custom_keyboard.append([c])
                reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter account to cancel monitoring", "reply_markup":reply_markup})
                unmon_pending.append(chat_id)
            elif cmd == "/subscription_list":
                list = ""
                if chat_id in subscribe_list:
                    subscribe_list[chat_id].sort()
                    for i in subscribe_list[chat_id]:
                        list += i+"\n"
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Your subscription list:\n" + list})
                else:
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are not subscribing"})
            elif cmd == "/cancel_subscription":
                custom_keyboard = []
                if chat_id in subscribe_list:
                    subscribe_list[chat_id].sort()
                    for c in subscribe_list[chat_id]:
                        custom_keyboard.append([c])
                reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                m = telegram("sendMessage", {"chat_id":chat_id, "text":"Enter category to cancel subscription", "reply_markup":reply_markup})
                unsub_pending.append(chat_id)
            elif chat_id in mon_pending:
                id = cmd.lower()
                skip = 0
                if id in monitor_id:
                    if chat_id in monitor_id[id]:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are already monitoring " + id})
                        skip = 1
                    else:
                        monitor_id[id].append(chat_id)
                        coll_monid.insert_one({"id": id, "tgid": chat_id})
                else:
                    monitor_id[id] = [chat_id]
                    coll_monid.insert_one({"id":id, "tgid":chat_id})
                if chat_id in monitor_list:
                    if id in monitor_list[chat_id]:
                        pass
                    else:
                        monitor_list[chat_id].append(id)
                else:
                    monitor_list[chat_id] = [id]
                if skip == 0:
                    custom_keyboard = ck(chat_id)
                    reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are now monitoring *" + id + "*", "reply_markup":reply_markup, "parse_mode":"Markdown", "disable_web_page_preview":True})
                mon_pending.remove(chat_id)
                skip = 0
            elif chat_id in sub_pending:
                id = cmd.lower()
                skip = 0
                if id in subscribe_id:
                    if chat_id in subscribe_id[id]:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are already subscribing " + id})
                        skip = 1
                    else:
                        subscribe_id[id].append(chat_id)
                        coll_subid.insert_one({"id": id, "tgid": chat_id})
                else:
                    subscribe_id[id] = [chat_id]
                    coll_subid.insert_one({"id":id, "tgid":chat_id})
                if chat_id in subscribe_list:
                    if id in subscribe_list[chat_id]:
                        pass
                    else:
                        subscribe_list[chat_id].append(id)
                else:
                    subscribe_list[chat_id] = [id]
                if skip == 0:
                    custom_keyboard = ck(chat_id)
                    reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are now subscribing _" + id + "_", "reply_markup":reply_markup, "parse_mode":"Markdown", "disable_web_page_preview":True})
                sub_pending.remove(chat_id)
                skip = 0
            elif chat_id in unmon_pending:
                id = cmd.lower()
                if id in monitor_id:
                    if chat_id in monitor_id[id]:
                        monitor_id[id].remove(chat_id)
                        monitor_list[chat_id].remove(id)
                        coll_monid.delete_one({"id": id, "tgid": chat_id})
                        custom_keyboard = ck(chat_id)
                        reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"Cancelled monitoring *" + id + "*", "reply_markup":reply_markup, "parse_mode":"Markdown", "disable_web_page_preview":True})
                    else:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are not monitoring " + id})
                else:
                    custom_keyboard = ck(chat_id)
                    reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Wrong account", "reply_markup":reply_markup})
                unmon_pending.remove(chat_id)
            elif chat_id in unsub_pending:
                id = cmd.lower()
                if id in subscribe_id:
                    if chat_id in subscribe_id[id]:
                        subscribe_id[id].remove(chat_id)
                        subscribe_list[chat_id].remove(id)
                        coll_subid.delete_one({"id": id, "tgid": chat_id})
                        custom_keyboard = ck(chat_id)
                        reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"Cancelled subscribing _" + id + "_", "reply_markup":reply_markup, "parse_mode":"Markdown", "disable_web_page_preview":True})
                    else:
                        m = telegram("sendMessage", {"chat_id":chat_id, "text":"You are not subscribing " + id})
                else:
                    custom_keyboard = ck(chat_id)
                    reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                    m = telegram("sendMessage", {"chat_id":chat_id, "text":"Wrong category", "reply_markup":reply_markup})
                unsub_pending.remove(chat_id)
            elif cmd.lower() == "/stats":
                msg = "Monitoring: " + str(len(monitor_list)) + " / Subscribing: " + str(len(subscribe_list)) + " / TPS: " + format(tps, ".2f")
                m = telegram("sendMessage", {"chat_id":chat_id, "text":msg})
            else:
                custom_keyboard = ck(chat_id)
                reply_markup = json.dumps({"keyboard":custom_keyboard, "resize_keyboard": True})
                msg = "Please choose your option or type /help"
                payload = {"chat_id":chat_id, "text":msg, "reply_markup":reply_markup}
                m = telegram("sendMessage", payload)
    return update_id


if __name__ == '__main__':

    ws = create_connection("ws://127.0.0.1:8090")
    last_update_id = 0
    client = MongoClient()
    db = client.notimeet
    coll_block = db.block
    coll_monid = db.monid
    coll_subid = db.subid
    monitor_id, subscribe_id, monitor_list, subscribe_list = db_gen()
    wid = 0
    try:
        block = coll_block.find()[0]["block"]
    except:
        sub = json.dumps({"jsonrpc": "2.0", "id": wid, "method": "call", "params": [0, "get_dynamic_global_properties", []]})
        send = ws.send(sub)
        wid += 1
        block = json.loads(ws.recv())["result"]["head_block_number"]
        coll_block.insert_one({"block":block})

    while True:
        sub = json.dumps({"jsonrpc": "2.0", "id": wid, "method": "call", "params": [0, "get_block", [block]]})
        send = ws.send(sub)
        wid += 1
        res = json.loads(ws.recv())
        ntx = 0
        if res["result"] != None:
            if res["result"]["transactions"] != []:
                tx = res["result"]["transactions"]
                ntx = len(tx)
                for i in range(ntx):
                    for o in range(len(tx[i]["operations"])):
                        op = tx[i]["operations"][o]
                        if op[0] == "comment":
                            for j in monitor_id:
                                if str("@"+j) in op[1]["body"]:
                                    author = op[1]["author"]
                                    plink = op[1]["permlink"]
                                    title = op[1]["title"]
                                    parent_author = op[1]["parent_author"]
                                    parent_permlink = op[1]["parent_permlink"]
                                    if title == "":
                                        try:
                                            tag = json.loads(op[1]["json_metadata"])["tags"][0]
                                            url = "https://steemit.com/%s/@%s/%s#@%s/%s" % (tag, parent_author, parent_permlink, author, plink)
                                            msg = "*%s* is mentioned by %s in [a comment](%s)\n%s" % (j, author, url, op[1]["body"][0:4000])
                                        except:
                                            msg = "*%s* is mentioned by %s in a comment\n%s" % (j, author, op[1]["body"][0:4000]) 
                                    else:
                                        url = "https://steemit.com/%s/@%s/%s" % (parent_permlink, author, plink)
                                        msg = "*%s* is mentioned by %s in a post\n[%s](%s)" % (j, author, title, url)
                                    for t in monitor_id[j]:
                                        payload = {"chat_id":t, "text":msg, "parse_mode":"Markdown", "disable_web_page_preview":True}
                                        telegram("sendMessage", payload)
                                if op[1]["title"] == "":
                                    if op[1]["parent_author"] == j and op[1]["body"][0:2] != "@@":
                                        author = op[1]["author"]
                                        plink = op[1]["permlink"]
                                        parent_author = op[1]["parent_author"]
                                        parent_permlink = op[1]["parent_permlink"]
                                        try:
                                            tag = json.loads(op[1]["json_metadata"])["tags"][0]
                                            url = "https://steemit.com/%s/@%s/%s#@%s/%s" % (tag, j, parent_permlink, author, plink)
                                            msg = "New comment by %s on *%s*'s [post/comment](%s)\n%s" % (author, j, url, op[1]["body"][0:4000])
                                        except:
                                            msg = "New comment by %s on *%s*'s post/comment\n%s" % (author, j, op[1]["body"][0:4000])
                                        for t in monitor_id[j]:
                                            payload = {"chat_id":t, "text":msg, "parse_mode":"Markdown", "disable_web_page_preview":True}
                                            telegram("sendMessage", payload)
                                else:
                                    if op[1]["author"] == j and op[1]["body"][0:2] != "@@":
                                        author = op[1]["author"]
                                        plink = op[1]["permlink"]
                                        parent_permlink = op[1]["parent_permlink"]
                                        msg = "[New post](https://steemit.com/%s/@%s/%s) by *%s*" % (parent_permlink, j, plink, j)
                                        for t in monitor_id[j]:
                                            payload = {"chat_id":t, "text":msg, "parse_mode":"Markdown"}
                                            telegram("sendMessage", payload)
                            for j in subscribe_id:
                                if (op[1]["parent_permlink"] == j or (j[-1] == "*" and op[1]["parent_permlink"][0:(len(j)-1)] == j[0:-1])) and op[1]["body"][0:2] != "@@":
                                    author = op[1]["author"]
                                    title = op[1]["title"]
                                    plink = op[1]["permlink"]
                                    msg = "New post in _%s_\nAuthor: %s\nTitle: [%s](https://steemit.com/%s/@%s/%s)" % (op[1]["parent_permlink"], author, title, op[1]["parent_permlink"], author, plink)
                                    for t in subscribe_id[j]:
                                        payload = {"chat_id":t, "text":msg, "parse_mode":"Markdown", "disable_web_page_preview":True}
                                        telegram("sendMessage", payload)

            block += 1
            coll_block.update_one({"block":block-1}, {"$set":{"block":block}})
            try:
                last_update_id = update_db(last_update_id)
            except:
                pass
            tpslist.append(ntx)
            tpslist = tpslist[-1200:]
            tps = sum(tpslist)/(len(tpslist)*3)
            print("Head block: " + str(block) + " / TPS: " + format(tps, ".2f") + "\r", end="")
        else:
            try:
                last_update_id = update_db(last_update_id)
            except:
                pass
            time.sleep(1)
