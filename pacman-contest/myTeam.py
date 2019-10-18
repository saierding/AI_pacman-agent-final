# myTeam.py



from captureAgents import CaptureAgent
import random, time, util
import math
from game import Directions,Actions
import  copy
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'Attacker', second = 'Defender'):
  

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):


  def registerInitialState(self, gameState):
    """
    定义一个起始情况，调用captureagent里的registerinitialstate 里面大概方法比如这个distanceCalculator算距离
    self.distancer.getDistance(p1, p2)，还有我们是红队还是蓝队isred. 然后我在这里给实例self加了个home表示家里，
    orignialfood用来返回所有food数就是对面的你要吃的。defendfood就是我们要防的。wall不解释了吧哈哈。lasteaten就是
    我好像也没用，eatenfood就是你吃到回去以后才会得到的food
    """
    CaptureAgent.registerInitialState(self, gameState)
    self.home = gameState.getAgentState(self.index).getPosition()
    self.originalFood=len(self.getFood(gameState).asList())
    self.defendFood=len(self.getFoodYouAreDefending(gameState).asList())
    self.walls = gameState.getWalls().asList()
    self.lastEaten=None
    self.eatenFood=None


  def getMiddleLines(self,gameState):
    """"
    获得中线，这个很好理解
    """
    if self.red:
      middleLine = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
    else:
      middleLine = [(gameState.data.layout.width / 2, y) for y in range(0, gameState.data.layout.height)]
    availableMiddle = [a for a in middleLine if a not in self.walls]
    return availableMiddle


  def getInvaders(self, gameState):
    """
    获得入侵者，返回一个敌人的gamestate信息，包括位置坐标，方向啥的
    """
    enemies = [gameState.getAgentState(o) for o in self.getOpponents(gameState)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    if len(invaders)==0:
      return None
    else:
      return invaders

  def getDefenders(self,gameState):
    """
    获得敌人防守者的信息如果距离在不是none的范围的话
    """
    enemies=[gameState.getAgentState(o) for o in self.getOpponents(gameState)]
    defenders=[a for a in enemies if a.getPosition() != None and not a.isPacman]
    if len(defenders)==0:
      return  None
    else:
      return defenders


  def getCloseFood(self, gameState):
    """
    返回一个最近的food的坐标
    """
    foods = [food for food in self.getFood(gameState).asList()]
    foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) for a in foods]
    closeFood = [f for f, d in zip(foods, foodDistance) if d == min(foodDistance)]
    if len(closeFood)==0:
      return None
    else:
      return closeFood[0]

  def getcloseCapsule(self,gameState):
    """
    返回一个最近的capsule的坐标，如果有的话哈哈
    """
    capsules = self.getCapsules(gameState)
    if len(capsules)==0:
      return None
    else:
      capsuleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), c) for c in capsules]
      closeCapsules=[c for c,d in zip(self.getCapsules(gameState),capsuleDis) if d==min(capsuleDis)]
      return closeCapsules[0]

  def getSuccessors(self, currentPosition):
    """
    返回下一步坐标和方向
    """
    successors = []
    forbidden =self.walls
    for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
      x, y = currentPosition
      dx, dy = Actions.directionToVector(action)
      nextx, nexty = int(x + dx), int(y + dy)
      if (nextx, nexty) not in forbidden:
        nextPosition = (nextx, nexty)
        successors.append((nextPosition, action))
    return successors


  def simpleHeuristic(self,gameState,thisPosition):
    return 0

  def enemyConcernHeuristic(self,gameState,thisPosition):
     """
     如果和defender距离小于3就给heuristics添加蛮大的值，要不就为0，返回最大的max
     """
     heuristics=[]
     ghost=self.getDefenders(gameState)
     if ghost==None :
       return 0
     else:
       for o in ghost:
        if self.getMazeDistance(thisPosition,o.getPosition())<3:
          d = self.getMazeDistance(thisPosition,o.getPosition())
          heuristics.append(math.pow((d-5),4))
        else:
          heuristics.append(0)
       #print (max(heuristics))
       return max(heuristics)


  def aStarSearch(self,gameState,goal,heuristic):
    """
    astar的方法，heuristic用上面的发现敌人赶紧跑的策略
    """
    start =self.getCurrentObservation().getAgentState(self.index).getPosition()
    openSet = util.PriorityQueue()
    openSet.push(( start,[]), 0)
    visitedNodes = []
    while not openSet.isEmpty():
      node,trace=openSet.pop()
      if node == goal:
        if len(trace)==0:
          return 'Stop'

        return trace[0]
      if node not in visitedNodes:
        visitedNodes.append(node)
        successors=self.getSuccessors(node)
        for successor in successors:
          cost= len(trace +[successor[1]])+heuristic(gameState,successor[0])
          if successor not in visitedNodes:
            openSet.push((successor[0], trace + [successor[1]]), cost)
    if goal != self.home:
      return self.aStarSearch(gameState,self.home,self.enemyConcernHeuristic)
    return 'Stop'


class Attacker(ReflexCaptureAgent):

  def chooseAction(self,gameState):
    """
    就这一个方法在这个里面。先是定义一堆后面要用的，其中middle就是距离最近的中线tuple用来溜的，没有以下的if特殊情况
    返回astar往中线一路狂飙就完事了
    """

    closeCapsule=self.getcloseCapsule(gameState)
    foods=self.getFood(gameState).asList()
    closeFood=self.getCloseFood(gameState)
    middleLines = self.getMiddleLines(gameState)
    middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), mi) for mi in
                 middleLines]
    closeMiddle = [m for m, d in zip(middleLines, middleDis) if d == min(middleDis)]
    middle = closeMiddle[0]
    defenders = self.getDefenders(gameState)
    #print (self.getDefenders(gameState))
    invaders=self.getInvaders(gameState)


    if gameState.getAgentState(self.index).scaredTimer > 0 and invaders != None and not gameState.getAgentState(self.index).isPacman:
      """
      第一个if，只要有敌人而且你不是pacman,而且你距离invader距离小于等于2，那你就出击去用astar追invader
      """
      for invader in invaders:
        if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                invader.getPosition()) <= 2:
          return self.aStarSearch(gameState, self.home, self.enemyConcernHeuristic)

    if self.getScore(gameState)<0:
      """
      第二个if，如果你的现在分数小于零了，而且如果你的带食物量减去分数大于0，或者带食物量大于10就把goal改成了middle赶紧往回溜
      """
      if gameState.getAgentState(self.index).numCarrying +self.getScore(gameState)>0:
        return self.aStarSearch(gameState, middle, self.enemyConcernHeuristic)


    if gameState.data.timeleft<200 or len(foods)<3 or gameState.getAgentState(self.index).numCarrying >5:
      """
      第三个if，如果时间小于200或者食物小于3个了，或者你带了超过28个食物了，这情况下如果你的带食物量大于0就把goal改成了middle赶紧往回溜
      """
      if gameState.getAgentState(self.index).numCarrying>0:
        return self.aStarSearch(gameState,middle,self.enemyConcernHeuristic)

    if defenders!=None:
      """
      第四个if，如果有defender然后defender还是出于害怕情况（吃了capsule了），goal继续为closefood,不用加maxheuristic
      否则goal为closefood，加上maxheuristic
      """
      for defender in defenders:
        if defender.scaredTimer >0:
          if defender.scaredTimer > 10:
            return self.aStarSearch(gameState,closeFood,self.simpleHeuristic)
          else:
            return self.aStarSearch(gameState, closeFood, self.enemyConcernHeuristic)

    if closeCapsule!=None:
      """
      第五个if, 如果有capsule，然后还有defender，如果defender距离capsule小于2了，返回goal为中线，astar一顿跑；要是距离不是
      小于2，来我们用astar对着closecapsule就是一顿追。
      """
      if defenders!=None:
        if gameState.getAgentState(self.index).numCarrying>5 or gameState.data.timeleft<500:
          return self.aStarSearch(gameState,closeCapsule,self.enemyConcernHeuristic)
        else:
          for d in defenders:
            if self.getMazeDistance(d.getPosition(),closeCapsule)<2:
            #print ('enemy close to cap,back')
              return self.aStarSearch(gameState, middle, self.enemyConcernHeuristic)
            #print ('eat cap')
          return self.aStarSearch(gameState,closeFood,self.enemyConcernHeuristic)

    if closeCapsule==None:
      """
      第六个if，如果有defender但是没有capsule了而且我们还带着吃的食物呢，astar中线跑就完事了
      """
      if defenders!=None and gameState.getAgentState(self.index).numCarrying !=0:
        #print ('chasen,back')
        return self.aStarSearch(gameState,middle,self.enemyConcernHeuristic)

    return self.aStarSearch(gameState,closeFood,self.enemyConcernHeuristic)


###########################################################################################################################################################################################################################################
class Defender(ReflexCaptureAgent):

  def isEating(self):
    """
    如果有以前一个的观察记录并且你保护的食物比前一个观察的食物少了返回true，意思有人吃豆了
    """
    if self.getPreviousObservation() is not None and len(self.getFoodYouAreDefending(self.getCurrentObservation()).asList())<len(self.getFoodYouAreDefending(self.getPreviousObservation()).asList()):
        return True
    else:
      return  False

  def setEaten(self,eaten):
    self.eatenFood=eaten

  def getEaten(self):
    """
    这里挺重要的，先找个当前的foodl列表，再找个前一个状态的food列表，再来循环前一个状态的看当前哪一个少了，那好，找到
    被吃的food了就，然后找距离就是eatenDis,找到距离最小的被吃的food记为closeEaten,并返回出来
    """
    defendLeft=self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    lastDefend=self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
    eaten=[left for left in lastDefend if left not in defendLeft]
    eatenDis=[self.getMazeDistance(self.getCurrentObservation().getAgentState(self.index).getPosition(),eat) for eat in eaten]
    closeEaten=[e for e ,d in zip(eaten,eatenDis) if d==min(eatenDis)]
    self.setEaten(closeEaten[0])
    return closeEaten[0]


  def beginEaten(self):
    """
    这个方法就是如果发现我们的食物被吃了就要返回true
    """
    if len(self.getFoodYouAreDefending(self.getCurrentObservation()).asList())<self.defendFood:
      return True
    else:
      return False

  def chooseAction(self, gameState):
    """
    这里和之前attacker一样先定义一些，基本都一样，还是没有特殊情况直接astar往中线是goal走就行了，不同的是，这里返回的heuristic
    不考虑敌人的，就是那个max_heuristic是attacker的，这里用的是simple.
    """
    invaders=self.getInvaders(gameState)

    middleLines = self.getMiddleLines(gameState)
    middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), mi) for mi in
                 middleLines]
    closeMiddle = [m for m, d in zip(middleLines, middleDis) if d == min(middleDis)]
    middle = closeMiddle[0]
    for index in self.getOpponents(gameState):
      """
      对每一个对手，如果对手带回的num比之前前一个状态下带回的num多，defendfood减去这已经被对手拿走的food
      """
      if self.getPreviousObservation() is not None:
        if gameState.getAgentState(index).numReturned>self.getPreviousObservation().getAgentState(index).numReturned:
          self.defendFood=self.defendFood-( gameState.getAgentState(index).numReturned-self.getPreviousObservation().getAgentState(index).numReturned)

    if gameState.getAgentState(self.index).getPosition()==middle or gameState.getAgentState(self.index).getPosition()==self.eatenFood:
      """
      如果防守者到中线上了或者到被吃的food那里了，就astar一直往家走
      """
      return self.aStarSearch(gameState,self.home,self.simpleHeuristic)

    if gameState.getAgentState(self.index).scaredTimer>0 and invaders!=None:
      """
      如果被别人吃了capsule处于冷却了，时间大于0并且有敌人入侵时，对每个入侵者距离小于2时，用maxheuristic往家里跑
      """
      for invader in invaders:
         if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                invader.getPosition()) <= 2:
           return self.aStarSearch(gameState,self.home, self.enemyConcernHeuristic)

    if invaders!=None:
      """
      如果有入侵者，target是距离最近的入侵者，然后astar对他进行追击
      """
      invadersDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a.getPosition()) for a in
                     invaders]
      minDIs = min(invadersDis)
      target = [a.getPosition() for a, v in zip(invaders, invadersDis) if v == minDIs]
      return self.aStarSearch(gameState,target[0],self.simpleHeuristic)

    if self.beginEaten():
      """
      如果食物被吃返回true了，并且如果有人正在吃食物则对eaten进行astar追击，否则对eatenfood进行追击
      """
      if self.isEating():
        eaten=self.getEaten()
        self.setEaten(eaten)
        return self.aStarSearch(gameState,eaten,self.simpleHeuristic)
      else:
        return self.aStarSearch(gameState,self.eatenFood,self.simpleHeuristic)

    return self.aStarSearch(gameState,middle,self.simpleHeuristic)