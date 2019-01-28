import random
import re
import time
import unittest
import uuid

from library.core.TestCase import TestCase
from library.core.common.simcardtype import CardType
from library.core.utils.applicationcache import current_mobile, switch_to_mobile
from library.core.utils.testcasefilter import tags
from pages import *

REQUIRED_MOBILES = {
    'Android-移动': 'M960BDQN229CH',
    # 'Android-移动': 'single_mobile',
    'IOS-移动': '',
    'Android-电信': 'single_telecom',
    'Android-联通': 'single_union',
    'Android-移动-联通': 'mobile_and_union',
    'Android-移动-电信': '',
    'Android-移动-移动': 'double_mobile',
    'Android-XX-XX': 'others_double',
}


class Preconditions(object):
    """前置条件"""

    @staticmethod
    def select_mobile(category, reset=False):
        """选择手机"""
        client = switch_to_mobile(REQUIRED_MOBILES[category])
        client.connect_mobile()
        if reset:
            current_mobile().reset_app()
        return client

    @staticmethod
    def make_already_in_one_key_login_page():
        """已经进入一键登录页"""
        # 如果当前页面已经是一键登录页，不做任何操作
        one_key = OneKeyLoginPage()
        if one_key.is_on_this_page():
            return

        # 如果当前页不是引导页第一页，重新启动app
        guide_page = GuidePage()
        if not guide_page.is_on_the_first_guide_page():
            # current_mobile().launch_app()
            current_mobile().reset_app()
            guide_page.wait_for_page_load(20)

        # 跳过引导页
        guide_page.wait_for_page_load(30)
        guide_page.swipe_to_the_second_banner()
        guide_page.swipe_to_the_third_banner()
        current_mobile().hide_keyboard_if_display()
        guide_page.click_start_the_experience()

        # 点击权限列表页面的确定按钮
        permission_list = PermissionListPage()
        permission_list.click_submit_button()
        one_key.wait_for_page_load(30)

    @staticmethod
    def login_by_one_key_login():
        """
        从一键登录页面登录
        :return:
        """
        # 等待号码加载完成后，点击一键登录
        one_key = OneKeyLoginPage()
        one_key.wait_for_tell_number_load(60)
        one_key.click_one_key_login()
        one_key.click_read_agreement_detail()

        # 同意协议
        agreement = AgreementDetailPage()
        agreement.click_agree_button()

        # 等待消息页
        message_page = MessagePage()
        message_page.wait_login_success(60)

    @staticmethod
    def make_already_in_message_page(reset=False):
        """确保应用在消息页面"""
        Preconditions.select_mobile('Android-移动', reset)
        current_mobile().hide_keyboard_if_display()
        time.sleep(1)
        # 如果在消息页，不做任何操作
        mess = MessagePage()
        if mess.is_on_this_page():
            return
        # 进入一键登录页
        Preconditions.make_already_in_one_key_login_page()
        #  从一键登录页面登录
        Preconditions.login_by_one_key_login()

    @staticmethod
    def make_already_have_my_group(reset=False):
        """确保有群，没有群则创建群名为mygroup+电话号码后4位的群"""
        # 消息页面
        Preconditions.make_already_in_message_page(reset)
        mess = MessagePage()
        mess.wait_for_page_load()
        # 点击 +
        mess.click_add_icon()
        # 点击 发起群聊
        mess.click_group_chat()
        # 选择联系人界面，选择一个群
        sc = SelectContactsPage()
        times = 15
        n = 0
        # 重置应用时需要再次点击才会出现选择一个群
        while n < times:
            flag = sc.wait_for_page_load()
            if not flag:
                sc.click_back()
                time.sleep(2)
                mess.click_add_icon()
                mess.click_group_chat()
                sc = SelectContactsPage()
            else:
                break
            n = n + 1
        sc.click_select_one_group()
        # 群名
        group_name = Preconditions.get_group_chat_name()
        # 获取已有群名
        sog = SelectOneGroupPage()
        sog.wait_for_page_load()
        group_names = sog.get_group_name()
        # 有群返回，无群创建
        if group_name in group_names:
            return
        sog.click_back()
        # 从本地联系人中选择成员创建群
        sc.click_local_contacts()
        slc = SelectLocalContactsPage()
        names = slc.get_contacts_name()
        if not names:
            raise AssertionError("No contacts, please add contacts in address book.")
        # 选择成员
        for name in names:
            slc.select_one_member_by_name(name)
        slc.click_sure()
        # 创建群
        cgnp = CreateGroupNamePage()
        cgnp.input_group_name(group_name)
        cgnp.click_sure()
        # 等待群聊页面加载
        GroupChatPage().wait_for_page_load()

    @staticmethod
    def enter_group_chat_page(reset=False):
        """进入群聊聊天会话页面"""
        # 确保已有群
        Preconditions.make_already_have_my_group(reset)
        # 如果有群，会在选择一个群页面，没有创建群后会在群聊页面
        scp = GroupChatPage()
        sogp = SelectOneGroupPage()
        if sogp.is_on_this_page():
            group_name = Preconditions.get_group_chat_name()
            # 点击群名，进入群聊页面
            sogp.select_one_group_by_name(group_name)
            scp.wait_for_page_load()
        if scp.is_on_this_page():
            return
        else:
            raise AssertionError("Failure to enter group chat session page.")

    @staticmethod
    def get_group_chat_name():
        """获取群名"""
        phone_number = current_mobile().get_cards(CardType.CHINA_MOBILE)[0]
        group_name = "chargourp" + phone_number[-4:]
        return group_name

class MsgGroupChatvedioTest(TestCase):
    """消息->群聊>图片&视频 模块"""
    """前置条件需要修改创建一个群找不到"""
    @classmethod
    def setUpClass(cls):
        pass

    def default_setUp(self):
        """确保每个用例运行前在群聊聊天会话页面"""
        Preconditions.select_mobile('Android-移动')
        scp = GroupChatPage()
        if scp.is_on_this_page():
            current_mobile().hide_keyboard_if_display()
            return
        else:
            try:
                Preconditions.select_mobile('Android-移动')
                Preconditions.enter_group_chat_page(reset=True)
            except Exception:
                try:
                    Preconditions.select_mobile('Android-移动')
                    Preconditions.enter_group_chat_page(reset=True)
                except Exception:
                    Preconditions.select_mobile('Android-移动')
                    Preconditions.enter_group_chat_page(reset=True)

    def default_tearDown(self):
        pass
        # current_mobile().disconnect_mobile()

    @tags('ALL', 'SMOKE', 'CMCC1', 'group_chat')
    def test_msg_group_chat_video_0001(self):
        """群聊会话页面，不勾选相册内图片点击发送按钮"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        # 4.判断发送按钮是否能点击
        flg=cpg.send_btn_is_enabled()
        self.assertEquals(flg, False)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0002(self):
        """群聊会话页面，勾选相册内一张图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(1)
        # 4.点击发送返回到群聊页面,校验是否发送成功
        cpg.click_send()
        gcp.is_on_this_page()
        self.assertEqual(gcp.is_send_sucess(),True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0003(self):
        """群聊会话页面，预览相册内图片"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk()
        # 4.点击预览
        cpg.click_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 5. 校验照片是否可以预览
        self.assertIsNotNone(cpp.get_pic_preview_info())

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0004(self):
        """群聊会话页面，预览相册内图片，不勾选原图发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk()
        # 4.点击预览
        cpg.click_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 5.点击发送,
        cpp.click_send()
        gcp.is_on_this_page()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0005(self):
        """群聊会话页面，预览相册数量与发送按钮数量一致"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择n<=9张相片
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(3)
        # 4.点击预览检验，预览相册数量与发送按钮数量一致
        cpg.click_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        ppi=cpp.get_pic_preview_num()
        ppn=cpp.get_pic_send_num()
        self.assertEquals(ppi, ppn)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0006(self):
        """群聊会话页面，编辑图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击预览
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk()
        cpg.click_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        # 5.点击文本编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我是python测试开发工程师")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_send()
        # 6 点击发送后，判断在群聊首页
        gcp.is_on_this_page()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0007(self):
        """群聊会话页面，编辑图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击点击打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(1)
        cpg.click_pic_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        time.sleep(1)
        # 5.点击文本编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我是python测试开发工程师")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_send()
        # 6 点击发送后，判断在群聊首页,校验是否发送成功
        gcp.wait_for_page_load()
        gcp.is_on_this_page()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0008(self):
        """群聊会话页面，编辑图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击点击打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(1)
        cpg.click_pic_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        # 5.点击图片编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我qqqqqqqq程师")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_save()
        cpe.click_picture_send()
        # 6 点击发送后，判断在群聊首页
        gcp.wait_for_page_load()
        gcp.is_on_this_page()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0009(self):
        """群聊会话页面，编辑图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击点击打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(1)
        cpg.click_pic_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        # 5.点击文本编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我是python测试开发工程师")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_save()
        cpe.click_picture_send()
        # 6 点击发送后，判断在群聊首页,校验是否发送成功
        gcp.wait_for_page_load()
        gcp.is_on_this_page()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0010(self):
        """群聊会话页面，取消编辑图片,不发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击点击打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk()
        cpg.click_pic_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        # 5.点击文本编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我是python测试开发工程师")
        time.sleep(1)
        cpe.click_picture_cancel()
        cpe.click_picture_cancel()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0011(self):
        """群聊会话页面，取消编辑图片,发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择一张相片,点击点击打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk()
        cpg.click_pic_preview()
        cpp = ChatPicPreviewPage()
        cpp.wait_for_page_load()
        # 4.点击编辑（预览图片）
        cpp.click_edit()
        cpe = ChatPicEditPage()
        # 5.点击文本编辑（预览图片）
        cpe.click_picture_edit()
        # a 涂鸦动作
        cpe.click_picture_edit_crred()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # b 马赛克动作
        cpe.click_picture_mosaic()
        cpe.click_picture_edit_switch()
        time.sleep(1)
        # c 文本编辑动作
        cpe.click_picture_text()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("我是python测试开发工程师")
        time.sleep(1)
        cpe.click_picture_cancel()
        cpe.click_picture_cancel()
        cpe.click_picture_select()
        cpe.click_picture_send()
        # 6 点击发送后，判断在群聊首页
        gcp.is_on_this_page()
        gcp.wait_for_page_load()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0012(self):
         """群聊会话页面，发送相册内的图片，校验预览格式"""
         # 1.检验是否当前聊天会话页面，
         gcp = GroupChatPage()
         gcp.is_on_this_page()
         # 2.点击输入框左上方的相册图标
         gcp.click_picture()
         # 3.进入相片页面,选择一张相片
         cpg = ChatPicPage()
         cpg.wait_for_page_load()
         cpg.select_pic_fk()
         # 4.点击点击打开,校验格式
         cpg.click_pic_preview()
         cpp = ChatPicPreviewPage()
         cpp.wait_for_page_load()
         flag=cpp.get_pic_preview_info()
         self.assertIsNotNone(re.match(r'预览\(\d+/\d+\)', flag))

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0013(self):
        """群聊会话页面，点击该相册内两张图片，点击预览，隐藏"编辑"按钮"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择2张相片,点击预览打开
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(n=2)
        cpg.click_preview()
        cpp = ChatPicPreviewPage()
        # 4.校验预览页面中隐藏"编辑"按钮的提示
        cpp.wait_for_page_load()
        cpp.click_edit()
        fla=cpp.edit_btn_is_toast()
        self.assertEqual(fla,True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0014(self):
        """群聊会话页面，勾选9张相册内图片发送"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择9张相片发送
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(n=9)
        cpg.click_send ()
        # 4.点击发送后，判断在群聊首页
        gcp.is_on_this_page()
        gcp.wait_for_page_load()
        self.assertEqual(gcp.is_send_sucess(), True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0015(self):
        """群聊会话页面，勾选10张相册内图片发送校验"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,选择大于或等于10张相片,校验提示：“最多只能选择9张照片”
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(10)
        flg1=cpg.is_toast_exist_maxp()
        self.assertEqual(flg1,True)
        flg2=cpg.get_pic_send_nums()
        self.assertEqual(flg2,'9')

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0016(self):
        """群聊会话页面，同时发送相册中的图片和视屏"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击输入框左上方的相册图标
        gcp.click_picture()
        # 3.进入相片页面,同时选择视频和图片
        cpg = ChatPicPage()
        cpg.wait_for_page_load()
        cpg.select_pic_fk(n=1)
        cpg.select_video_fk(n=1)
        flag=cpg.is_toast_exist_pv()
        self.assertEqual(flag,True)

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0017(self):
        """群聊会话页面，使用拍照功能拍照发送照片"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击点击富媒体行拍照图标
        gcp.click_take_photo()
        # 3.进入相机拍照页面，点击拍照
        cpp = ChatPhotoPage()
        cpp.wait_for_page_load()
        cpp.take_photo()
        cpp.send_photo()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0018(self):
        """群聊会话页面，使用拍照功能拍照编辑后发送照片"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击点击富媒体行拍照图标
        gcp.click_take_photo()
        # 3.进入相机拍照页面，点击拍照
        cpp = ChatPhotoPage()
        cpp.wait_for_page_load()
        cpp.take_photo()
        cpp.click_edit_pic()
        cpe = ChatPicEditPage()
        cpe.click_text_edit_btn()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("正在编辑图片")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_send()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0019(self):
        """群聊会话页面，使用拍照功能拍照编辑后发送照片"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击点击富媒体行拍照图标
        gcp.click_take_photo()
        # 3.进入相机拍照页面，点击拍照
        cpp = ChatPhotoPage()
        cpp.wait_for_page_load()
        cpp.take_photo()
        cpp.click_edit_pic()
        cpe = ChatPicEditPage()
        cpe.click_text_edit_btn()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("正在编辑图片")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_save()
        cpe.click_send()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0020(self):
        """群聊会话页面，使用拍照功能拍照编辑后发送照片"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击点击富媒体行拍照图标
        gcp.click_take_photo()
        # 3.进入相机拍照页面，点击拍照
        cpp = ChatPhotoPage()
        cpp.wait_for_page_load()
        cpp.take_photo()
        cpp.click_edit_pic()
        cpe = ChatPicEditPage()
        cpe.click_text_edit_btn()
        cpe.click_picture_edit_crred()
        cpe.input_picture_text("正在编辑图片")
        time.sleep(1)
        cpe.click_picture_save()
        cpe.click_picture_cancel()
        time.sleep(1)
        cpp.send_photo()

    @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    def test_msg_group_chat_video_0022(self):
        """群聊会话页面，打开拍照，拍照之后返回会话窗口"""
        # 1.检验是否当前聊天会话页面，
        gcp = GroupChatPage()
        gcp.is_on_this_page()
        # 2.点击点击富媒体行拍照图标
        gcp.click_take_photo()
        # 3.进入相机拍照页面，点击取消拍照
        cpp = ChatPhotoPage()
        cpp.wait_for_page_load()
        cpp.take_photo_back()
        # 4.校验是否已经返回到聊天页面
        gcp.is_on_this_page()

    # @tags('ALL', 'SMOKE', 'CMCC', 'group_chat')
    # def test_msg_group_chat_video_0023(self):
    #     """群聊会话页面，转发他人发送的图片给本地联系人"""
    #     # 1.检验是否当前聊天会话页面
    #     gcp = GroupChatPage()
    #     gcp.is_on_this_page()
    #     # 2.长按他人所发的图片
    #     gcp.press_pic()
    #     gcp.click_forward()
    #     scg = SelectContactsPage()
    #     scg.wait_for_page_load()
    #     scg.select_local_contacts()


