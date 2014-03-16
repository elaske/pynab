#!/usr/bin/python

"""
Parse YNAB4's budget data to work out how much is left in the current month.

Designed for an Alfred 2 Workflow

Written by James Seward 2013-07; http://jamesoff.net; @jamesoff
Thanks to @ppiixx for pointing out/fixing the rollover problem :)

BSD licenced, have fun.

Uses the alp library from https://github.com/phyllisstein/alp; thanks Daniel!
"""

import json
import datetime
import os.path
import locale
import sys
import logging

def debug_print(text):
    logging.debug(text)


def new_walk_budget(data, category):
    """
    New algorithm:
      Walk all available months
        If an amount is budgeted, add to running total
        Play all the transactions in that category for that month
        If at the end the balance is negative:
          If overspendingHandling is null, reset balance to 0
          If overspendingHandling is "confined", keep balance
    """
    budget = 0
    saved_budget = None
    now = datetime.date.today()

    debug_print("-- Starting walk_budget for %s" % category)

    monthly_budgets = sorted(data["monthlyBudgets"], key=lambda k: k["month"])

    for month in monthly_budgets:
        Y = int(month["month"][0:4])
        M = int(month["month"][5:7])
        budget_month = datetime.date(Y, M, 1)
        if budget_month > now:
            # Now we've reached the future so time to stop
            debug_print("Reached the future")
            if not saved_budget == None and budget == 0:
                budget = saved_budget
            break
        debug_print("")
        debug_print("Starting %s with budget of %0.2f" % (month["month"], budget))
        budget += get_monthly_budget(month["monthlySubCategoryBudgets"], category)
        debug_print("Budgeted amount for %s is %0.2f" %(month["month"], budget))
        budget += play_monthly_transactions(data, month["month"][0:7], category)
        debug_print("Ended month with balance of %0.2f" % budget)
        if budget < 0:
            debug_print("Category is overspent for this month!")
            osh = get_overspending_handling(month["monthlySubCategoryBudgets"], category)

            if not osh == None and (not osh.lower() == "confined"):
                debug_print("Resetting balance to 0")
                saved_budget = budget
                budget = 0

    debug_print("Finished walking budget, balance is %0.2f" % budget)
    return budget


def play_monthly_transactions(data, month, categoryId):
    """
    Play all the transactions in a category for a month, including
    split transactions. Return the total of those transactions.
    """
    balance = 0
    found_data = False
    try:
        transactions = data["transactions"]
        for transaction in transactions:
            this_month = transaction["date"][0:7]
            if this_month == month:
                if transaction["categoryId"] == "Category/__Split__":
                    for sub_transaction in transaction["subTransactions"]:
                        if sub_transaction["categoryId"] == categoryId and not "isTombstone" in sub_transaction:
                            balance += sub_transaction["amount"]
                            debug_print("  Found split transaction %s (%s)" % (sub_transaction["amount"], balance))
                else:
                    if transaction["categoryId"] == categoryId and not "isTombstone" in transaction:
                        balance += transaction["amount"]
                        debug_print("  Found transaction %s (%s)" % (transaction["amount"], balance))
    except Exception, e:
        debug_print(e)
        handle_error("Error finding budget balance", "", "icon-no.png", e)
        debug_print("oh no")

    debug_print("Monthly spend for this category is %0.2f" % balance)

    return balance


def get_monthly_budget(data, category):
    """
    Find the amount allocated to a category for a month.
    """
    for subcategory in data:
        if subcategory["categoryId"] == category:
            return subcategory["budgeted"]
    return 0

def get_overspending_handling(data, category):
    """
    Find the overspendingHandling for a category in a month
    """
    for subcategory in data:
        if subcategory["categoryId"] == category:
            if "overspendingHandling" in subcategory:
                return subcategory["overspendingHandling"]
            else:
                return None
    return None


def handle_error(title, subtitle, icon = "icon-no.png", debug = ""):
    """
    Output an error message in a form suitable for Alfred to show something.
    Send the error and any debug info supplied to the log file.
    """
    i = alp.Item(title = title, subtitle = subtitle, icon = icon)
    alp.feedback(i)
    alp.log("Handled error: %s, %s\n%s" % (title, subtitle, debug))
    sys.exit(0)


def find_budget(path):
    """
    Given a path (to a YNAB budget bundle) load the meta data and try to 
    find a datafile with full knowledge we can work from.
    """
    # Look in the ymeta file to find our data directory
    try:
        fh = open(os.path.join(path, "Budget.ymeta"), "r")
        info = json.load(fh)
        fh.close()
    except Exception, e:
        if fp:
            fp.close()
        handle_error("Unable to find budget file :(", path, "icon-no.png", e)

    folder_name = info["relativeDataFolderName"]
    
    # Now look in the devices folder, and find a folder which has full knowledge
    devices_path = os.path.join(path, folder_name, "devices")
    devices = os.listdir(devices_path)
    use_folder = ""

    try:
        for device in devices:
            fh  = open(os.path.join(devices_path, device))
            device_info = json.load(fh)
            if device_info["hasFullKnowledge"]:
                use_folder = device_info["deviceGUID"]
                break
    except Exception, e:
        handle_error("Unable to read budget data", "Parse error looking for full knowledge", "icon-no.png", e)

    if use_folder == "":
        handle_error("Unable to find usable budget data", "", "icon-no.png")

    return os.path.join(path, folder_name, use_folder)


def load_budget(path):
    """
    Load a budget file in to memory.
    """
    try:
        fp = open(os.path.join(path, "Budget.yfull"), "r")
        data = json.load(fp)
        fp.close()
    except Exception, e:
        if fp:
            fp.close()
        handle_error("Unable to find budget file :(", path, "icon-no.png", e)

    return data


def get_currency_symbol(data):
    """
    Try to guess the currency symbol for this budget file based on its
    locale.
    """
    try:
        currency_locale = data["budgetMetaData"]["currencyLocale"]
        locale.setlocale(locale.LC_ALL, locale.normalize(currency_locale))
    except Exception, e:
        pass


def all_categories(data):
    """
    Find all the categories in a budget file.
    """
    all = []
    try:
        master_categories = data["masterCategories"]
        for master_category in master_categories:
            if master_category["name"] in ["Pre-YNAB Debt", "Hidden Categories"]:
                continue
            sub_categories = master_category["subCategories"]
            if sub_categories != None:
                for sub_category in master_category["subCategories"]:
                    if "isTombstone" in sub_category and sub_category["isTombstone"]:
                        continue
                    all.append({"entityId": sub_category["entityId"], "name": sub_category["name"]})
    except Exception, e:
        handle_error("Error reading budget categories", "", "icon-no.png", e)

    return all


def find_category(data, category_name):
    """
    Locate a particular category and return the ID for it.
    """
    entityId = ""
    try:
        master_categories = data["masterCategories"]
        for master_category in master_categories:
            sub_categories = master_category["subCategories"]
            if sub_categories != None:
                for sub_category in master_category["subCategories"]:
                    if sub_category["name"] == category_name and not "isTombstone" in sub_category and not sub_category["isTombstone"]:
                        entityId = sub_category["entityId"]
                        break
            if entityId != "":
                break
        if entityId == "":
            pass
    except Exception, e:
        pass

    if entityId == "":
        handle_error("Error finding budget category", "", "icon-no.png", e)

    return entityId


def check_for_budget(path):
    """
    Look in a folder to see if it contains a budget we can use.
    """
    result_path = ""
    if os.path.exists(path):
        sub_folders = os.listdir(path)
        if ".DS_Store" in sub_folders:
            sub_folders.remove(".DS_Store")
        if "Exports" in sub_folders:
            sub_folders.remove("Exports")
        if len(sub_folders) == 1:
            path = os.path.join(path, sub_folders[0])
            result_path = find_budget(path)
    return result_path


if __name__ == "__main__":   
    path = ''
    
    # If we have a setting for the location, use that
    if not path == "":
        path = find_budget(path)

    # Else, we guess...
    # First we look in Dropbox
    if path == "":
        path = check_for_budget(os.path.expanduser("~/Dropbox/YNAB"))

    # Then we look locally
    if path == "":
        path = check_for_budget(os.path.expanduser("~/Documents/YNAB"))

    # Then we give up
    if path == "":
        handle_error("Unable to guess budget location", "Use Alfred's File Action on your budget file to configure", "icon-no.png")

    # Load data
    debug_print(path)
    data = load_budget(path)
    get_currency_symbol(data)

    all = all_categories(data)
    debug_print(all)