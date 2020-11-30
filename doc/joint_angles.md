# JointAngles

`from magnebot.joint_angles import JointAngles`

The angles and targets of a Magnebot joint.
This is useful mainly for the backend code when tracking whether joints have stopped moving.

***

## Fields

- `angles` The current angles of a joint in degrees as a numpy array.. If this is a revolute or prismatic joint, this has 1 element. If this is a spherical joint, this has 3 elements: `[x, y, z]`.

- `targets` The current target angles of a joint in degrees as a numpy array.. If this is a revolute or prismatic joint, this has 1 element. If this is a spherical joint, this has 3 elements: `[x, y, z]`.

***

## Functions

#### \_\_init\_\_

**`def __init__(self, angles: np.array, targets: np.array)`**

| Parameter | Description |
| --- | --- |
| angles | The current angles of the joint. |
| targets | The target angles of the joint. |

