# ROS 2 interface testing

Test the smallest observable contract first: message type, topic/service/action name, QoS compatibility, launch wiring, and timing. Use deterministic fixtures where possible and record what was actually observed rather than inferring runtime health.
