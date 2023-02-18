def create_user(tx, username):
    tx.run("CREATE (a:User {username: $username})", username=username)


def create_pending(tx, username, to_username):
    tx.run("MATCH (x:User) WHERE x.username = $username "
           "MATCH (y:User) WHERE y.username = $to_username "
           "MERGE (x)-[:Pending]->(y) ",
           username=username, to_username=to_username)
    tx.run("MATCH (x)-[rel:Pending]->(x) "
           "DELETE rel")


def create_friend(tx, username, friend):
    tx.run('MATCH (x:User) where x.username = $username '
           'MATCH (y:User) where y.username = $friend '
           'MATCH (x)<-[rel:Pending]-(y) '
           'MERGE (x)<-[:Friend]-(y) ' 
           'MERGE (x)-[:Friend]->(y) '
           'DELETE rel ',
           username=username, friend=friend)
    tx.run('MATCH (x:User) where x.username = $username '
           'MATCH (y:User) where y.username = $friend '
           'MATCH (x)-[rel:Pending]->(y) '
           'DELETE rel ',
           username=username, friend=friend)

def l_friend(tx, username, friend):
    tx.run('MATCH (x:User) where x.username = $username '
           'MATCH (y:User) where y.username = $friend '
           'MATCH (x)<-[rel1:Friend]-(y) '
           'MATCH (x)-[rel2:Friend]->(y) '
           'DELETE rel1, rel2',
           username=username, friend=friend)

def get_pending(tx, username):
    pending = []
    result = tx.run('MATCH (x:User) WHERE x.username = $username ' 
                    'MATCH (x)<-[:Pending]-(y) return y AS pending', username=username)
    for record in result:
        pending.append(record["pending"])
    return pending

def get_outgoing(tx, username):
    outgoing = []
    result = tx.run('MATCH (x:User) WHERE x.username = $username ' 
                    'MATCH (x)-[:Pending]->(y) return y AS outgoing', username=username)
    for record in result:
        outgoing.append(record["outgoing"])
    return outgoing

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
