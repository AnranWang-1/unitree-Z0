ls /dev/video*

ffplay /dev/video4

python unitree_lerobot/eval_robot/eval_arm.py   --policy.path=/home/unitree/unitree_IL_lerobot_back/unitree_lerobot/lerobot/outputs/train/2026-03-10/16-39-32_act/checkpoints/last/pretrained_model   --repo_id=PICK   --frequency=30   --visualization=false   --arm=UNIARM   --ee=""   --send_real_robot=true   --uniarm_urdf_path=/home/unitree/unitree/lerobot/uni-arm/robot.urdf   --uniarm_mesh_dir=/home/unitree/unitree/lerobot/uni-arm/   --uniarm_port=/dev/ttyACM1 --visualization=True   --uniarm_head_camera_id=3   --uniarm_wrist_camera_id=1