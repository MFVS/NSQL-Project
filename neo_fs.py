def create_user(tx, username):
    tx.run("CREATE (a:User {username: $username})", username=username)


def create_pending(tx, username, to_username):
    tx.run("MATCH (x:User), (y:User) WHERE x.username = $username AND y.username = to_username"
           "CREATE (x)-[:Pending]->(y)",
           username=username, to_username=to_username)


def create_friend(tx, username, friend):
    tx.run('MATCH (x:Person), (y:Person) where x.username = username and y.username = friend'
           'match (x)-[rel:friend]->(y) '
           'create (x)-[:pending]->(y) delete rel',
           username=username, friend=friend)


def get_pending(tx, username):
    pending = []
    result = tx.run("MATCH (x:User)-[:pending]->(y) "
                    "WHERE x.username = $username "
                    "RETURN y.username AS pending", username=username)
    for record in result:
        pending.append(record["pending"])
    return pending

def get_friends(tx, username):
    friends = []
    result = tx.run("MATCH (x:User)-[:friend]->(y) "
                    "WHERE x.username = $username "
                    "RETURN y.username AS friend", username=username)
    for record in result:
        friends.append(record["friend"])
    return friends