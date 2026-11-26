# The SOLIDWORKS welcome window can outlive a capture

A short capture can finish while SOLIDWORKS still has startup windows.
A successful post to the verified frame only confirms that Windows queued the
close request.

The driving-dimension singleton saved its baseline and returned from
`QuitDoc` on SOLIDWORKS 34.4.1.1011. The welcome window was visible and
its owner was the verified frame. After the worker posted its first close
request, the welcome window became hidden. The frame and exact process remained
alive through the 30-second deadline. A separate singleton replay reproduced
the timeout. The worker classified each attempt as failed.

A second normal close did not resolve the timeout. The welcome window
observation does not establish a cause. The standalone worker succeeded on a
fresh second attempt. A later combined replay read an empty document set
after `QuitDoc`. Calling `ExitApp` at that point produced both normal process
exits without needing a window close. Batch capture also uses the bounded
controller retry. Each failed attempt remains separate from accepted evidence.
[Shutdown evidence](../../../../Changes/Research/Supervisor/Catalogue/SolidWorksCaptureShutdown.md)
