"""
Joke tool — built-in Chinese joke bank with online API fallback.
"""

import random
import httpx


# Offline Chinese joke bank — always available, no network needed
_JOKES_ZH = [
    "我问我的狗：谁是这个世界上最好的孩子？它说：汪！",
    "程序员为什么不喜欢出门？因为外面没有WiFi密码。",
    "咖啡对杯子说：你装什么呢？杯子说：我装的是你呀。",
    "为什么数学书总是很悲伤？因为它有太多的问题。",
    "两根香蕉走在路上，前面那根说：我好热啊。后面那根说：你当然热，你还穿着外套呢。",
    "我告诉医生我胳膊断了，医生问：哪个胳膊？我说：就是这根。医生说：说得好。",
    "大海为什么是蓝色的？因为鱼儿在里面吐泡泡：blue blue blue。",
    "小明问妈妈：为什么我的名字叫小明？妈妈说：因为你出生的时候天刚好亮了。小明说：那如果天没亮呢？妈妈说：那你就会叫小暗。",
    "病人：医生，我一吃鸡蛋就肚子疼。医生：你是怎么吃鸡蛋的？病人：连壳一起吃。",
    "老师：请用「如果」造个句子。学生：如果我中了五百万，我就买下这个学校。老师：然后呢？学生：然后让老师写作业。",
    "蜗牛对妈妈发脾气：我受够了，我要离家出走！妈妈说：别闹，房子还在你背上呢。",
    "手机和充电器约会。手机说：我需要你。充电器说：我只是一个过客，充满我就走。",
    "蚊子对爸爸说：爸，我想喝可乐。爸爸说：我们家世代喝血的，你别忘本！蚊子说：那我加点冰。",
    "什么东西越洗越脏？答案是水。",
    "为什么鸡过马路？因为要去对面找肯德基投诉。",
    "男朋友说：亲爱的，我离不开你，就像鱼离不开水。女朋友：那我们分手吧。男朋友：为什么？女朋友：因为你是两栖动物。",
    "面试官：你有什么特长？我：我吃得特别多。面试官：这算什么特长？我：这不算特长的话，那我能睡特别久。",
    "树上有两只鸟，一只对另一只说：你唱得真好听。另一只说：谢谢，我也是这么觉得的。第一只说：自信是好事，但过度自信就是噪音了。",
    "猫对老鼠说：你为什么不跑？老鼠说：因为我在等一个奇迹。猫说：什么奇迹？老鼠说：你突然变成素食主义者。",
    "老师：小明，地球为什么是圆的？小明：因为如果它是方的，走在边上的同学会掉下去。",
]


def get_joke() -> str:
    """Return a random Chinese joke. Uses built-in bank, falls back to API."""
    # 90% chance: use built-in bank (faster, no network)
    if random.random() < 0.9:
        return random.choice(_JOKES_ZH)

    # 10% chance: try online API for variety
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(
            "https://official-joke-api.appspot.com/random_joke"
        )
        response.raise_for_status()
        data = response.json()
        setup = data.get("setup", "")
        punchline = data.get("punchline", "")
        if setup and punchline:
            return f"这里有个笑话：{setup}  ——  {punchline}"
    except Exception:
        pass

    return random.choice(_JOKES_ZH)
