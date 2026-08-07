# Set DEBUG = True to bypass assessment ordering restrictions.
# In debug mode, all mechanisms and tasks are enabled regardless of completion order.
# Set to False to restore normal sequential assessment behavior.
DEBUG = True

# Guided GUI mechanism order — DEBUG only, ignored entirely when DEBUG is False.
#
#   None            walk the normal order for the mode:
#                       screening   HOC, FPS, WFE, WURD
#                       assessment  WURD, WFE, FPS, HOC
#
#   ["HOC"]         walk only these mechanisms, in this order, in BOTH modes.
#   ["HOC", "FPS"]  Use it to reach the mechanism under test without sitting
#                   through the other three.
#
# Valid names: "FPS", "WFE", "WURD", "HOC". An unknown or repeated name is
# rejected when the session starts, rather than quietly running a different
# order than the one you typed.
#
# The session's protocol CSV still contains every mechanism — only the walk is
# shortened — so a run with this set does NOT complete the timepoint.
MECHANISM_ORDER = ["HOC", "FPS", "WFE", "WURD"]
