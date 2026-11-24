# The SOLIDWORKS welcome window can outlive a capture

A short capture can finish while SOLIDWORKS still has startup windows.
A successful post to the verified frame only confirms that Windows queued the
close request.

The driving-dimension singleton saved its baseline and returned from
`QuitDoc` on SOLIDWORKS 34.4.1.1011. The welcome window was visible and
its owner was the verified frame. After the worker posted its first close
request, the welcome window disappeared. The frame and exact process remained
alive through the 30-second deadline. A separate singleton replay reproduced
the timeout. The worker classified each attempt as failed.

The worker can request a second normal close halfway through the existing
close-wait interval when the process remains alive. It rechecks the same
process creation identity and frame ownership for each request. The worker
still requires the retained process handle to signal by the existing deadline.
[Shutdown evidence](../../../../Changes/Research/Supervisor/Catalogue/SolidWorksCaptureShutdown.md)
