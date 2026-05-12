主从遥操做
/home/unitree/unitree/xr_teleoperate_new/teleop/test_teleop.py

异构遥操
/home/unitree/unitree/xr_teleoperate_new/teleop/test_IK_placo_pico.py


检查端口
/home/unitree/unitree/uni-arm/motor_driver/check_port.py

sudo chmod 666 /dev/ttyUSB*

通信测试
/home/unitree/unitree/uni-arm/motor_driver/con_circle.py

校准文件
/home/unitree/.cache/huggingface/lerobot/calibration/robots/uniarm_follower/follower.json


校准程序
/home/unitree/unitree/lerobot/src/lerobot/scripts/uniarm_calibrate.py（有bug）


# 2026.4.13
## 1. 确定串口：
```bash
python teleop/check_port_all.py
```

## 2. 检验跳变
首先是VR遥操，跳变非常严重
```python
python teleop/teleop_arm.py
```
具体呈现以下几点：
1. 启动后直接转到一个很怪的位置，so系列启动之后会移动到所有电机的中位，这样vr在空间中任意移动都有余量
2. 遥操时轻微转动手柄就会带来很大的动作，需要放小一些
3. ctrl+c退出后，会回到那个奇怪的初始位置
4. wrist_pitch发热相当严重，甚至将打印件烫软，需要将下方两个螺丝都固定，然后加上holder--ljz
5. 电机散热功能很差，断电5min后才降为正常温度

1和3其实是一个问题，启动脚本之后的初始位置可能本是由一个关节引起的，可能是wrist_pitch(3)，和elbow_flex(2,7),个人倾向于motor3,他旋转导致elbow电机被迫转动，elbow被抬升。

初始姿态定义：
可以通过修改：teleop_arm line167：self.q_init_sim_rad = np.array([0.0, 0.0, 0.0, -2.3, 0.0, -0.1898])
self.q_init_sim_rad = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) 初始位置确实改动了，但是ctrl+c之后会爆回一个位置


## 3. 解决1和3--启动与退出导致的跳变
### 3.1 启动跳变
首先得解决这个启动之后会突变的问题，有两种方案
1. 类似so101，启动之后除gripper之外都转动到校准中位，gripper（5）最好能保持让夹爪张开的值
2. 保存一个home位，启动和退出时都回到这个位置，home则为自然状态下电机的位置
两种都可以实现一下，然后用命令行参数选择哪种方式然后添加到脚本中。

方案一：需要将脚本写到tests/teleop中，需要一个脚本计算出校准中位，然后控制电机移动到那个位置，控制频率固定，可以通过时间修改到位速度。

我发现目前使用的方案2,但是具体的初始位置有点迷惑，应该是一个写死的位置，并非通过校准计算，shoulder_pan 和 wrist_roll的 0.0 是正常的，shouler_lift的0为什么会抬起来，但是又不是中间，elbow_flex的0也不是中间，具体可以看图，wrist_flex的-2.3是向上的。

推理和urdf中关节范围有关:

关节	           类型	         URDF 范围	    说明
shoulder_pan	revolute	[-1.816, 1.674]	底座旋转    0 的话大概在中间
shoulder_lift	revolute	[-2.737, 0.929]	肩关节俯仰  中间应为 -0.904
elbow_flex	    revolute	[-0.580, 2.737]	肘关节弯曲  中间应为 1.0785
wrist_flex	    revolute	[-3.142, 0]	    腕关节俯仰  中间应为 -1.571
wrist_roll	    revolute	[-3.142, 3.142]	腕关节旋转  0 在中间
gripper	        revolute	[-3.142, 3.142]	夹爪       0 在中间

修改成中间值试一下：
self.q_init_sim_rad = np.array([0.0, -0.904, 1.0785, -1.571, 0.0, 0.0])
大概是伸直了，但是吧，可能由于重力影响，或力矩控制下的特性，并非纯中位：

shouler_lift    前倾，0为后倾             -0.904< <0
elbow_flex      前倾，0前的多，1前的少     >1
wrist_flex      -2.3后倾多，-1.571后倾少  >-1.571

但是这么改，确实可以让电机在中间，但有点丑陋，可能是war说的那个问题。

新增功能
1. 配置参数 - config_uniarm.py:36-38
init_move_duration: float = 2.0  # 移动时间（秒）

2. 平滑移动方法 - uniarm.py:776-824
follower.move_to_init_position(duration=2.0)  # 可自定义时间
这个pd没有进行修改，导致这个过程有点抖动。

3. 调用 - teleop_arm.py:52
follower.move_to_init_position()

这个方法也是大概移动到目标位置，后续原来的移动到初始位置微调到位，防止直接冲到目标位置。

### 3.2 退出跳变
在 stop_control_loop() 中添加了判断，如果是力矩控制，直接失能进入刹车模式，不会瞬间跌落也不需要修改home_set，若用home_set确实会回到位置，但是这个位置还得调整。

### 3.3 遥操过程中
shouler_pan     不敏感，而且转不到所有空间      问题不大，没必要修改逆解得分
shouler_lift    太敏感
elbow_flex      太敏感
wrist_flex      应反向
wrist_roll      没反应
gripper         正常，按下夹住

也可以加一个默认构型的权重，希望他在默认构型下解算ik，默认构型可以是常用的抓取物品的姿态。

### 3.4 尝试键盘调式
依据python teleop/teleop_arm.py写出用键盘遥操代码，看看是否有很严重的跳变问题
```bash
python teleop/teleop_arm_keyboard.py
```


## 4. 修改硬件模型
upper_arm + motor_holder

# 2026.4.14
## 1. 确定修改目标
调节参数使得末端摇操下能够像原方案一样稳定完成pickNplace，有可能需要调整逆解得分和pd参数
## 2. 需要注意的问题
1. 初始位置需修改一下，尽可能贴合弹簧方案位置，在摇操时也尽可能让机械臂回到这个位置再放开squzze
2. 尽可能移动vr手柄观察机械臂反应
3. 调节pd策略

刹车失能：
```bash
python tests/motor/disable_all.py
```

首先是得调整初始位置，当前为urdf范围的一半：
self.q_init_sim_rad = np.array([0.0, -0.904, 1.0785, -1.571, 0.0, 0.0])

尝试一下理想状态：
self.q_init_sim_rad = np.array([0.0, 0.0, 0.5, -1.2, 0.0, 0.0])

是合理的，但是启动时移动到这个位置有点太暴力了，振荡很大。

把这个注释掉好多了：
    # follower.move_to_init_position()

**启动和退出现在都没问题了**，那么尝试一下遥操作过程中有没有问题，这里应该就可以修改pd参数或ik权重了。

2. 不戴头显时，手柄前后移动时，机械臂没有反应；戴头显时有反应了
3. 不按下squzze，gripper也可以被trigger控制

总感觉头显的位置会影响VR操作的末端，可能存在坐标对应关系，启动脚本时让头显面向机械臂应该比较合理，

手腕roll，没什么用，手柄左右平移没什么用，手柄上下平移也没什么用？？？

手柄左右yaw可以控制shouler_pan，手柄pitch可以控制远近（勉强，仅限于在shouler_pan为0时不会太影响高度），当左右旋转之后，这个俯仰还会导致高度变化，手柄roll没用。

我更想知道每个关节哪些手柄变量影响的
shouler_pan     手柄yaw
shouler_lift
elbow_flex
wrist_flex      
wrist_roll      只有在一些极限位置会动
gripper         trigger

关节状态：
wrist_roll振荡较大，需要压住，d增大

手柄动的很小，shoulder_lift和elbow_flex动的很大

## 3. debug_ik.py中的问题
1. 手柄滚转时，wrist_roll没反应
2. 手柄yaw时，shouler_pan正常，shouler_lift和elbow_flex有时会直接伸直
3. 手柄前后推，现在有时能够控制前后，有时不能
4. 手柄的俯仰功能基本正常

wrist_roll


wrist_flex
1. 动作较大，需要降低VR映射系数
2. 观察到sim里转180,real里转90

elbow_flex
1. 动作较大，需要降低VR映射系数

shouler_lift
1. 动作略小

联调：
1. 上下时elbow_flex,shoulder_lift p不够
2. shoulder_lift一直不够
3. gripper 一开始是闭合状态
