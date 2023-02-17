def create_user(tx, username):
    tx.run("CREATE (a:User {username: $username})", username=username)


def create_pending(tx, username, to_username):
    tx.run("MATCH (x:User) WHERE x.username = $username "
           "MATCH (y:User) WHERE y.username = $to_username "
           "CREATE (x)-[:Pending]->(y)",
           username=username, to_username=to_username)


def create_friend(tx, username, friend):
    tx.run('MATCH (x:User) where x.username = $username '
           'MATCH (y:User) where y.username = $friend '
           'MATCH (x)<-[rel:Pending]-(y) '
           'CREATE (x)<-[:Friend]-(y) ' 
           'CREATE (x)-[:Friend]->(y) '
           'DELETE rel',
           username=username, friend=friend)


def get_pending(tx, username):
    pending = []
    result = tx.run('MATCH (x:User) WHERE x.username = $username ' 
                    'MATCH (x)<-[:Pending]-(y) return y AS pending', username=username)
    for record in result:
        pending.append(record["pending"])
    return pending

def get_friends(tx, username):
    friends = []
    result = tx.run('MATCH (x:User) WHERE x.username = $username ' 
                    'MATCH (x)<-[:Friend]-(y) return y AS friend', username=username)
    for record in result:
        friends.append(record["friend"])
    return friends

# untested
def delete_all_duplicate_relationships(tx):
    result = tx.run("""
match (s)-[r]->(e)
with s,e,type(r) as typ, tail(collect(r)) as coll 
foreach(x in coll | delete x)""")
    return result
