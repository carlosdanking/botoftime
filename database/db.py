from datetime import datetime, timedelta

class DataBase(object):
  def __init__(self,bot_database):
    self.database = bot_database
    self.db = self.database.Project1
    self.collection = self.db.users
  
  async def new_user(self,user_id,first_name,username):
    if not await self.collection.find_one({"user_id":user_id}):
      await self.collection.insert_one({"user_id":user_id,"firstname":first_name,"username":username,"join_date":None})
  
  async def global_bot(self):
    await self.collection.insert_one({"bot":"global"})
  
  async def get_bot(self):
    return await self.collection.find_one({"bot":"global"})
  
  async def get_user(self,user_id):
    return await self.collection.find_one({"user_id":user_id})
  
  async def set_new_key(self, key, val, user_id):
    await self.collection.update_one({"user_id":user_id},{"$set":{key:val}})
  
  async def set_bot_key(self, key, val):
    await self.collection.update_one({"bot":"global"},{"$set":{key:val}})
  
  async def update_bot(self):
    async for result in self.collection.find({}):
      if not result.get("user_id"):
        continue
      user_id = result["user_id"]
      await self.collection.delete_one({"user_id":user_id})
  
  async def verify(self):
    vencidos = []
    async for result in self.collection.find({}):
      if not result.get("user_id"):
        continue
      user_id = result["user_id"]
      join_date = result["join_date"]
      if join_date != None:
        now = datetime.now()
        day_since = (now - join_date).days
        if day_since >= 30:
          vencidos.append(user_id)
          await self.collection.update_one({"user_id":user_id},{"$set":{"join_date":None}})
    return vencidos