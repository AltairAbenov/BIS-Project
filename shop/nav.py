"""
Menu links in the top bar (whole team).
Each part of the site adds its own links here, so nobody has to edit base.html:
    add_link("My orders", "customer.my_orders", roles=("customer",))
"""
NAV = []


def add_link(label, endpoint, roles):
    NAV.append({"label": label, "endpoint": endpoint, "roles": tuple(roles)})


def links_for(role):
    return [n for n in NAV if role in n["roles"]]
