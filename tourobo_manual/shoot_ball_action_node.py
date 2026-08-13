import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from my_robot_interfaces.action import ShootBall


class ShootController(Node):

    def __init__(self):
        super().__init__('shoot_ball')

        # 実行中かどうかを判定するフラグ
        self.is_executing = False

        # 実行コールバックの処理中にも、キャンセルや別Goalの通信を並行して受け取れるようにする設定
        self.cb_group = ReentrantCallbackGroup()

        # Action Serverのインスタンス化
        self.action_server = ActionServer(
            self,
            ShootBall,
            'shoot_ball',  # Clientが呼び出すアクション名
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,  # 追加: Goal受信時のコールバック
            callback_group=self.cb_group)

    def goal_callback(self, goal_request):
        """新しいGoalリクエストを受け取ったときの判定処理"""
        if self.is_executing:
            self.get_logger().warn('現在別のShoot処理を実行中です。新しい指令を拒否します。')
            return GoalResponse.REJECT

        self.get_logger().info('新しいShoot指令を受け付けました。')
        return GoalResponse.ACCEPT

    async def shoot_ball(self):
        # ここに動作 (例: 少し時間がかかる処理を想定)
        # await asyncio.sleep(2.0) などの非同期処理が入る想定
        pass

    async def execute_callback(self, goal_handle):
        # 処理開始時にフラグを立てる
        self.is_executing = True

        req = goal_handle.request
        res = ShootBall.Result()
        success = False

        if req.mode == 1:
            success = await self.shoot_ball()

        res.success = success
        if success:
            goal_handle.succeed()
        else:
            goal_handle.abort()

        self.is_executing = False

        return res


def main(args=None):
    rclpy.init(args=args)
    node = ShootController()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


def stop():
    # 元コードにあった関数
    # set_stop_mode()
    # set_stop_mode()
    pass


if __name__ == '__main__':
    main()
