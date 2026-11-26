const { setTimeout: WaitPause } = require("node:timers/promises");
const { CheckQueueIdle } = require("./CheckQueueIdle.cjs");

async function WaitForQueue(
  Github,
  Context,
  Logger,
  Pause = WaitPause,
  Clock = Date.now,
) {
  const Deadline = Clock() + 60 * 60 * 1000;
  while (true) {
    if (Clock() >= Deadline)
      throw new Error(
        "Manual audit admission timed out; queue acceptance retained priority",
      );
    const IdleState = await CheckQueueIdle(Github, Context.repo);
    if (Clock() >= Deadline)
      throw new Error(
        "Manual audit admission timed out; queue acceptance retained priority",
      );
    if (IdleState) break;
    Logger.info(
      "Manual audit waiting for merge acceptance to release shared runners",
    );
    await Pause(Math.min(30000, Deadline - Clock()));
  }
  Logger.info("Manual audit admitted with bounded shared worker lanes");
}

module.exports = { WaitForQueue };
