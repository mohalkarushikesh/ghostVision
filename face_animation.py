
import cv2
import random
import math

# Persistent animation state
blink_timer = 0
is_blinking = False
next_blink_frame = 0


def draw_ghost_face(frame, cx, cy, scale, is_speaking, frame_count):
    global blink_timer, is_blinking, next_blink_frame

    # Ensure facial features remain visible on small detections.
    scale = max(8, int(scale))

    # --------------------------------------------------------
    # BLINK LOGIC
    # --------------------------------------------------------
    if not is_blinking:
        # Initialize the first blink schedule.
        if next_blink_frame == 0:
            next_blink_frame = frame_count + random.randint(40, 100)

        if frame_count >= next_blink_frame:
            is_blinking = True
            blink_timer = 3
    else:
        blink_timer -= 1

        if blink_timer <= 0:
            is_blinking = False
            next_blink_frame = frame_count + random.randint(40, 100)

    # Don't blink while speaking.
    if is_speaking:
        is_blinking = False

    # --------------------------------------------------------
    # GREEN GLOW
    # --------------------------------------------------------
    glow_radius = max(20, int(scale * 2.8))

    cv2.circle(
        frame,
        (cx, cy),
        glow_radius,
        (0, 255, 100),
        2,
        cv2.LINE_AA
    )

    # --------------------------------------------------------
    # EYES
    # --------------------------------------------------------
    eye_offset_x = scale
    eye_offset_y = scale
    eye_width = max(3, int(scale * 0.8))
    eye_height = max(2, int(scale * 0.8))

    left_eye = (cx - eye_offset_x, cy - eye_offset_y)
    right_eye = (cx + eye_offset_x, cy - eye_offset_y)

    if is_speaking:
        # EVIL MODE: glowing red eyes.
        cv2.ellipse(
            frame, left_eye,
            (eye_width, eye_height),
            0, 0, 360, (0, 0, 255), -1, cv2.LINE_AA
        )

        cv2.ellipse(
            frame, right_eye,
            (eye_width, eye_height),
            0, 0, 360, (0, 0, 255), -1, cv2.LINE_AA
        )

        # ----------------------------------------------------
        # ANIMATED MOUTH
        # ----------------------------------------------------
        # Smoothly vary the mouth opening.
        mouth_open = int(
            scale * (0.35 + 0.45 * abs(math.sin(frame_count * 0.8)))
        )

        mouth_width = max(4, int(scale * 0.9))

        cv2.ellipse(
            frame,
            (cx, cy + scale),
            (mouth_width, mouth_open),
            0, 0, 360,
            (0, 0, 0),
            -1,
            cv2.LINE_AA
        )

        # Red mouth outline for a more sinister look.
        cv2.ellipse(
            frame,
            (cx, cy + scale),
            (mouth_width, mouth_open),
            0, 0, 360,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )

    else:
        # IDLE MODE: blink by flattening the eyes.
        current_eye_height = 2 if is_blinking else eye_height

        cv2.ellipse(
            frame, left_eye,
            (eye_width, current_eye_height),
            0, 0, 360, (0, 0, 255), -1, cv2.LINE_AA
        )

        cv2.ellipse(
            frame, right_eye,
            (eye_width, current_eye_height),
            0, 0, 360, (0, 0, 255), -1, cv2.LINE_AA
        )

        # Subtle idle smile.
        cv2.ellipse(
            frame,
            (cx, cy + scale),
            (max(3, scale // 2), max(2, scale // 4)),
            0, 15, 165,
            (0, 255, 100),
            2,
            cv2.LINE_AA
        )
