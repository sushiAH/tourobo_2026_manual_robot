import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Joy
from action_msgs.msg import GoalStatus

# 追加: async/await をデッドロックさせずに使うためのモジュール
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from my_robot_interfaces.action import ShootBall


class RobotActionClient(Node):

    def __init__(self):
        super().__init__('joystick_action_client')

        # ★修正ポイント1: 並行処理グループの作成
        # コールバック内で await を使う場合、これを設定しないと通信がデッドロックします
        self._cb_group = ReentrantCallbackGroup()

        # 1. Action Clientのセットアップ (callback_group を指定)
        self._action_client_shoot = ActionClient(self,
                                                 ShootBall,
                                                 'shoot_ball',
                                                 callback_group=self._cb_group)

        # 2. JoyトピックのSubscriber (callback_group を指定)
        self._joy_sub = self.create_subscription(Joy,
                                                 'joy',
                                                 self.joy_callback,
                                                 10,
                                                 callback_group=self._cb_group)

        # 3. 状態管理用の変数
        self._prev_button_state = 0  # 前回のボタンの状態
        self._is_action_running = False  # Actionが実行中かどうかのフラグ

        self.get_logger().info('Joystick Action Client is ready.')

    # --- Action実行用の共通内部メソッド ---
    async def send_action_goal(self, client, goal_msg, action_name):
        """Actionを送信し、完了(SUCCEEDED)まで待機する共通処理"""
        self.get_logger().info(f"[{action_name}] サーバーを待機中...")
        if not client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error(f"[{action_name}] サーバーが見つかりません")
            return False

        self.get_logger().info(f"[{action_name}] ゴール送信開始")
        send_goal_future = await client.send_goal_async(goal_msg)

        if not send_goal_future.accepted:
            self.get_logger().error(f"[{action_name}] 命令が拒否されました")
            return False

        self.get_logger().info(f"[{action_name}] 受理されました。結果を待機します...")
        result_handle = await send_goal_future.get_result_async()

        # ステータスコードのチェック
        if result_handle.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"[{action_name}] 正常完了しました")
            return result_handle.result
        else:
            self.get_logger().warn(
                f"[{action_name}] 失敗しました (Status ID: {result_handle.status})")
            return None

    # 射出機構への指示出し
    async def send_to_shoot(self, mode):
        # ★修正ポイント2: クラス内のGoal型は 先頭大文字の Goal() です
        goal_msg = ShootBall.Goal()
        goal_msg.mode = mode
        return await self.send_action_goal(self._action_client_shoot, goal_msg,
                                           "shoot_ball")

    async def joy_callback(self, msg):
        """
        ジョイスティックの入力が来るたびに呼ばれるコールバック
        """
        current_button_state = msg.buttons[0]

        # 「前回が0」かつ「今回が1」のときだけ発火（立ち上がりエッジ検出）
        if self._prev_button_state == 0 and current_button_state == 1:

            # さらに、現在Actionが実行中でない場合のみGoalを送信する
            if not self._is_action_running:
                self.get_logger().info('ボタンが押し込まれました！指示を送信します。')

                # ★修正ポイント3: 実行中フラグをTrueにする（連打防止の要）
                self._is_action_running = True

                try:
                    await self.send_to_shoot(1)
                finally:
                    # ★修正ポイント4: 完了後（成功でもエラーでも）に必ずフラグをFalseに戻す
                    self._is_action_running = False
            else:
                self.get_logger().warn('現在動作中のため、入力を無視しました。')

        # 今回のボタン状態を「前回の状態」として保存して次回に備える
        self._prev_button_state = current_button_state


def main(args=None):
    rclpy.init(args=args)
    # ★修正ポイント5: 未定義の RobotClient() を RobotActionClient() に修正
    node = RobotActionClient()

    # ★修正ポイント6: await を使うためのマルチスレッド実行環境の設定
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()  # rclpy.spin(node) の代わりにこちらを使う
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt, shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
