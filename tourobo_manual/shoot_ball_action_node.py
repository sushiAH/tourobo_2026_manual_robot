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

        # 実行コールバックの処理中にも、キャンセルや別Goalの通信を並行して受け取れるようにする設定
        self.cb_group = ReentrantCallbackGroup()

        # Action Serverのインスタンス化
        self.action_server = ActionServer(
            self,
            ShootBall,
            'shoot_ball',  # Clientが呼び出すアクション名
            execute_callback=self.execute_callback,
            callback_group=self.cb_group)

    async def shoot_ball(self):
        #ここに動作
        pass

    async def execute_callback(self, goal_handle):
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

        return res


def main(args=None):
    rclpy.init(args=args)
    node = ShootController()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


def stop():
    set_stop_mode()
    set_stop_mode()


if __name__ == '__main__':
    main()
