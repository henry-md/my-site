# Hero "Me" Video Occlusion

Bug: the flying "Me" photo and callout could appear on top of the above-fold demo videos, especially near the chess demo, making the videos look transparent instead of fully in front.

Cause: the hover reliability fix raised `.hero-section-break-flyer` above `.hero-video-collage`, so the flyer painted over the video frames. The video cards use light/transparent-looking media styling, but their frame layer should still occlude anything passing behind them.

Fix: keep the video collage stacked above the flyer in the final hero override. Pointer hover reliability should come from the JS live-bounds tracker, not from placing the flyer above the videos.
