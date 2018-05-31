# importing main ros packages
import os
import rospkg
import rospy
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseWithCovarianceStamped

# importing ui packages
from qt_gui.plugin import Plugin
from python_qt_binding.QtWidgets import *
from python_qt_binding.QtGui import *
from python_qt_binding.QtCore import *

# importing json to read room coordinates
import json


# Main Plugin class
class MyPlugin(Plugin):
    def __init__(self, context):
        super(MyPlugin, self).__init__(context)

        # Give QObjects reasonable names
        self.setObjectName('MyPlugin')
        rp = rospkg.RosPack()

        self.stuck_status_count = 0
        self.current_odom_msg = 0
        self.previous_odom_msg = 0
        self.ongoing_delivery_status = False
        self.start_reached_status = False
        self.goal_reached_status = False
        self.dock_reached_status = False
        self.start_call = False
        self.goal_call = False
        self.dock_call = False
        self.start_room = ""
        self.goal_room = ""
        self.docking_station = {"dock": {"position_x": 0.0, "position_y": 0.0, "position_z": 0.0,
                                         "orientation_x": 0.0, "orientation_y": 0.0, "orientation_z": 0.0,
                                         "orientation_w": 1.0}}

        # getting room coordinate json
        room_json = os.path.join(rp.get_path('rqt_mypkg'), 'resource', 'room.json')
        self.room_coordinates = self.get_room_coordinates(room_json)

        # subscribing to "amcl_pose" and callback to update the pose of turtlebot
        self.sub = rospy.Subscriber('amcl_pose', PoseWithCovarianceStamped, self.odom_pose_callback)
        # defining publisher to publish destination pose
        self.pub = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=1)

        # Create QWidget
        self.widget = QWidget()
        context.add_widget(self.widget)

        # Layout and attach to widget
        layout = QVBoxLayout()
        self.widget.setLayout(layout)

        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)

        self._delivery_msg = QMessageBox()
        self._emergency_msg = QMessageBox()
        self._help_msg = QMessageBox()

        self._startOption = QComboBox()
        for key in self.room_coordinates.keys():
            self._startOption.addItem(key)
        self.grid_layout.addWidget(self._startOption, 1, 3)

        self.start_room = self._startOption.currentText()

        self._goalOption = QComboBox()
        for key in self.room_coordinates.keys():
            self._goalOption.addItem(key)
        self.grid_layout.addWidget(self._goalOption, 2, 3)

        self.goal_room = self._goalOption.currentText()

        self._start_button = QPushButton("GotoStart")
        self._start_button.clicked.connect(self.accept_start)
        self.grid_layout.addWidget(self._start_button, 1, 4)

        self._goal_button = QPushButton("GotoGoal")
        self._goal_button.clicked.connect(self.accept_goal)
        self.grid_layout.addWidget(self._goal_button, 2, 4)

        self._dock_button = QPushButton("GotoDock")
        self._dock_button.clicked.connect(self.accept_dock)
        self.grid_layout.addWidget(self._dock_button, 4, 3)

        self._emergency_button = QPushButton("Emergency Stop")
        self._emergency_button.clicked.connect(self.all_stop)
        self.grid_layout.addWidget(self._emergency_button, 4, 4)

        img_file = os.path.join(rp.get_path('rqt_mypkg'), 'resource', 'TurtleBot.jpg')
        self._pic_label = QLabel()
        self._pixmap = QPixmap(img_file)
        self._pixmap = self._pixmap.scaled(256, 192)
        self._pic_label.setPixmap(self._pixmap)
        # self.label.resize(100, 50)
        self.grid_layout.addWidget(self._pic_label, 2, 0, 3, 1)

        self._font = QFont()
        self._font.setBold(True)
        self._font.setPointSize(20)
        self._head_label = QLabel()
        self._head_label.setFont(self._font)
        self._head_label.setText('M2D2 - DELIVERY ROBOT\n'
                                 'MEI-56306 2017-01 Robotics Project Work')
        self.grid_layout.addWidget(self._head_label, 0, 0, 1, 1)

        self._font.setBold(False)
        self._font.setPointSize(12)
        self._text_label = QLabel()
        self._text_label.setFont(self._font)
        self._text_label.setText('SELECT THE PACKAGE RECEIVING LOCATION AND THE DELIVERY LOCATION\n'
                                 '* To call the robot press "gotoStart"\n'
                                 '* Once package is placed on robot press "gotoGoal"\n'
                                 '* Once the package is received at destination press "gotoDock"\n'
                                 '* On Emergency press Emergency stop \n'
                                 '* Appropriate msg will be displayed')
        self.grid_layout.addWidget(self._text_label, 1, 0, 1, 1)

    def get_room_coordinates(self, data_location):
        room_dict = dict()
        with open(data_location) as json_data:
            data = json.load(json_data)
            for key in data.keys():
                room_dict.update({key: data[key]})
        return room_dict

    def accept_start(self):
        if not self.ongoing_delivery_status:
            self.start_call = True
            self.goal_call = False
            self.dock_call = False
            self.ongoing_delivery_status = False
            self.start_room = self._startOption.currentText()
            self.go_to(self.room_coordinates[self.start_room])

    def accept_goal(self):
        if not self.ongoing_delivery_status and self.start_reached_status:
            self.goal_call = True
            self.start_call = False
            self.dock_call = False
            self.ongoing_delivery_status = True
            self.goal_room = self._goalOption.currentText()
            self.go_to(self.room_coordinates[self.goal_room])

    def accept_dock(self):
        if not self.ongoing_delivery_status and self.goal_reached_status:
            self.dock_call = True
            self.start_call = False
            self.goal_call = False
            self.ongoing_delivery_status = False
            self.goal_room = self._goalOption.currentText()
            self.go_to(self.docking_station['dock'])

    def odom_pose_callback(self, data):
        diff_y = 100
        diff_x = 100

        if self.current_odom_msg != 0:
            self.previous_odom_msg = self.current_odom_msg
            pos_x = self.previous_odom_msg.pose.pose.position.x
            pos_y = self.previous_odom_msg.pose.pose.position.y
            pos_to_go_x = self.room_coordinates[self.start_room]['position_x']
            pos_to_go_y = self.room_coordinates[self.start_room]['position_y']
            diff_x = abs(pos_x - pos_to_go_x)
            diff_y = abs(pos_y - pos_to_go_y)
            print self.current_odom_msg
        self.current_odom_msg = data

        if self.previous_odom_msg.pose.pose.position.x == self.current_odom_msg.pose.pose.position.x:
            self.stuck_status_count = self.stuck_status_count + 1
        else:
            self.stuck_status_count = 0

        if diff_x < 1.0 and diff_y < 1.0 and self.start_call:  # implement this function
            print "start point reached"
            self.start_reached_status = True
            self.goal_reached_status = False
            self.dock_reached_status = False

        if diff_x < 1.0 and diff_y < 1.0 and self.goal_call:  # implement this function
            print "goal point reached"
            self.goal_reached_status = True
            self.start_reached_status = False
            self.dock_reached_status = False
            self.ongoing_delivery_status = False

        if diff_x < 1.0 and diff_y < 1.0 and self.dock_call:  # implement this function
            self.dock_reached_status = True
            self.start_reached_status = False
            self.goal_reached_status = False
            print "dock point reached"

        if self.stuck_status_count > 1000 and not self.start_reached_status \
                and not self.goal_reached_status and not self.dock_reached_status:
            self._help_msg.setIcon(QMessageBox.Information)
            self._help_msg.setText('help me I am stuck')
            self.grid_layout.addWidget(self._delivery_msg, 2, 2)

    def go_to(self, destination):
        if self.start_call or self.goal_call or self.dock_call:
            print "in go_to"
            self._delivery_msg.setIcon(QMessageBox.Information)
            self._delivery_msg.setText('Delivery Process Initiated')
            self.grid_layout.addWidget(self._delivery_msg, 2, 2)
            self.turtlebot_call(destination)
            rospy.sleep(5)

    def turtlebot_call(self, coordinates):
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.z = coordinates['position_z']
        goal.pose.position.x = coordinates['position_x']
        goal.pose.position.y = coordinates['position_y']
        goal.pose.orientation.w = coordinates['orientation_w']
        print goal
        self.pub.publish(goal)
        rospy.sleep(5)

    def all_stop(self):
        self._emergency_msg.setIcon(QMessageBox.Warning)
        self._emergency_msg.setText('Delivery Process Initiated, Aborting all process')
        self.grid_layout.addWidget(self._emergency_msg, 1, 2)
        rospy.signal_shutdown("emergency stop pressed")
        self.shutdown_plugin()

    def shutdown_plugin(self):
        # TODO unregister all publishers here
        self._timeline.handle_close()
        pass

    def save_settings(self, plugin_settings, instance_settings):
        # TODO save intrinsic configuration, usually using:
        # instance_settings.set_value(k, v)
        pass

    def restore_settings(self, plugin_settings, instance_settings):
        # TODO restore intrinsic configuration, usually using:
        # v = instance_settings.value(k)
        pass

        # def trigger_configuration(self):
        # Comment in to signal that the plugin has a way to configure
        # This will enable a setting button (gear icon) in each dock widget title bar
        # Usually used to open a modal configuration dialog
