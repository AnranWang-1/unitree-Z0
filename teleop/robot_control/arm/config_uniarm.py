"""UniArm robot configuration — all-in-one config module.

修改此文件中的默认值即可调整所有参数，无需额外 YAML 文件。

Contains:
- RobotConfig: base class with subclass registry
- UniArmConfig: UniArm hardware parameters (serial port, motors, PD gains, etc.)
- UniArmRobotConfig: composed config (RobotConfig + UniArmConfig)
- TeleopConfig: teleop flow configuration (input mode, cameras, recording, etc.)
"""

from dataclasses import dataclass, field
from typing import Callable, ClassVar, TypeAlias, TypeVar

from image_server.camera import CameraConfig


# ── Robot config base ──────────────────────────────────────────

T = TypeVar("T", bound="RobotConfig")


@dataclass
class RobotConfig:
    """Base class for robot configurations with subclass registry."""

    _registry: ClassVar[dict[str, type["RobotConfig"]]] = {}

    id: str | None = None

    @classmethod
    def register_subclass(cls, key: str) -> Callable[[type[T]], type[T]]:
        """Decorator to register a subclass with a key."""
        def decorator(subclass: type[T]) -> type[T]:
            cls._registry[key] = subclass
            return subclass
        return decorator

    @classmethod
    def get_subclass(cls, key: str) -> type["RobotConfig"] | None:
        return cls._registry.get(key)


# ── UniArm hardware config ─────────────────────────────────────

@dataclass
class UniArmConfig:
    """UniArm 机械臂硬件配置。"""

    # 串口端口
    port: str

    disable_torque_on_disconnect: bool = True

    # 安全限制：最大单步目标变化幅度
    max_relative_target: float | dict[str, float] | None = None

    # 摄像头配置
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    # 角度单位
    use_degrees: bool = False

    urdf_path: str | None = None

    use_vr: bool = False

    # 初始化移动时间（秒）：从当前位置平滑移动到初始位置的时间
    # 设置为 0 表示立即跳转（可能导致抖动）
    init_move_duration: float = 2.0

    # 电机配置：关节名 -> 电机ID列表（支持双电机）
    # 双电机关节：两个电机同步驱动同一关节
    joint_motor_ids: dict[str, list[int]] = field(default_factory=lambda: {
        "shoulder_pan": [0],
        "shoulder_lift": [1, 6],  # 双电机
        "elbow_flex": [2, 7],     # 双电机
        "wrist_flex": [3],
        "wrist_roll": [4],
        "gripper": [5],
    })

    # 电机 PD 控制参数（按电机 ID 顺序，索引即为电机 ID）
    kp_loop: list[float] | None = None
    kd_loop: list[float] | None = None

    # 电机默认 kp/kd（用于电机控制模式）
    kp_default: list[float] | None = None
    kd_default: list[float] | None = None

    # 是否在没有真实机械臂的情况下运行（仿真模式）
    no_real_robot: bool = False


@RobotConfig.register_subclass("uniarm_follower")
@dataclass
class UniArmRobotConfig(RobotConfig, UniArmConfig):
    pass


UniArmConfigType: TypeAlias = UniArmRobotConfig


# ── Teleop flow config ─────────────────────────────────────────

@dataclass
class TeleopConfig:
    """遥操作流程配置 — 修改默认值即可调整参数。"""

    input: str = "vr"  # vr | keyboard | leader
    port: str = "/dev/ttyACM0"  # Follower arm serial port
    leader_port: str = "/dev/ttyACM3"  # Leader arm serial port
    urdf_path: str = "../assets/uni-arm/urdf/urdf_v0.7.urdf"
    cameras: list[str] = field(default_factory=lambda: ["head:2"])
    no_camera: bool = False
    record: bool = False
    task_dir: str = "./data/teleop"
    task_goal: str = ""
    record_hz: int = 50
    meshcat: bool = False
    no_real_robot: bool = False
