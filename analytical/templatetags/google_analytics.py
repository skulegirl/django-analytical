"""
Google Analytics template tags and filters.
"""

from __future__ import absolute_import

import decimal
import re

from django.conf import settings
from django.template import Library, Node, TemplateSyntaxError

from analytical.utils import (
    AnalyticalException,
    disable_html,
    get_domain,
    get_required_setting,
    is_internal_ip,
)

TRACK_SINGLE_DOMAIN = 1
TRACK_MULTIPLE_SUBDOMAINS = 2
TRACK_MULTIPLE_DOMAINS = 3

SCOPE_VISITOR = 1
SCOPE_SESSION = 2
SCOPE_PAGE = 3

PROPERTY_ID_RE = re.compile(r'^UA-\d+-\d+$')
SETUP_CODE = """
    <script type="text/javascript">

        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

        %(commands)s

    </script>
"""
CREATE_CODE = "ga('create', '%(property_id)s', 'auto' %(additional_args)s);"
SEND_PAGEVIEW_CODE = "ga('send', 'pageview');"
DOMAIN_CODE = "ga('linker:autoLink', ['%s']);"
REQUIRE_LINKER_CODE = "ga('require', 'linker');"
CUSTOM_VAR_CODE = "ga('set', '%(name)s', '%(value)s');"
ANONYMIZE_IP_CODE = "ga('set', 'anonymizeIp', true);"

ZEROPLACES = decimal.Decimal('0')
TWOPLACES = decimal.Decimal('0.01')

register = Library()


@register.tag
def google_analytics(parser, token):
    """
    Google Analytics tracking template tag.

    Renders Javascript code to track page visits.  You must supply
    your website property ID (as a string) in the
    ``GOOGLE_ANALYTICS_PROPERTY_ID`` setting.
    """
    bits = token.split_contents()
    if len(bits) > 1:
        raise TemplateSyntaxError("'%s' takes no arguments" % bits[0])
    return GoogleAnalyticsNode()


class GoogleAnalyticsNode(Node):
    def __init__(self):
        self.property_id = get_required_setting(
            'GOOGLE_ANALYTICS_PROPERTY_ID', PROPERTY_ID_RE,
            "must be a string looking like 'UA-XXXXXX-Y'")

    def render(self, context):
        commands = self._get_domain_commands(context)
        commands.extend(self._get_custom_var_commands(context))
        commands.extend(self._get_other_commands(context))
        html = SETUP_CODE % {
            'commands': " ".join(commands),
        }
        if is_internal_ip(context, 'GOOGLE_ANALYTICS'):
            html = disable_html(html, 'Google Analytics')
        return html

    def _get_domain_commands(self, context):
        commands = []
        tracking_type = getattr(settings, 'GOOGLE_ANALYTICS_TRACKING_STYLE',
                                TRACK_SINGLE_DOMAIN)
        commands.append(self._get_create_command(context, tracking_type))
        if tracking_type != TRACK_SINGLE_DOMAIN:
            commands.append(REQUIRE_LINKER_CODE)
            domain = get_domain(context, 'google_analytics')
            if domain is None:
                raise AnalyticalException(
                    "tracking multiple domains with Google Analytics requires a domain name")
            commands.append(DOMAIN_CODE % domain)
        commands.append(SEND_PAGEVIEW_CODE)
        return commands

    def _get_create_command(self, context, tracking_type):
        argstrings = []
        if tracking_type != TRACK_SINGLE_DOMAIN:
            argstrings.append("'allowLinker': true")

        sampleRate = getattr(settings, 'GOOGLE_ANALYTICS_SAMPLE_RATE', False)
        if sampleRate is not False:
            value = decimal.Decimal(sampleRate)
            if not 0 <= value <= 100:
                raise AnalyticalException("'GOOGLE_ANALYTICS_SAMPLE_RATE' must be >= 0 and <= 100")
            argstrings.append("'sampleRate' : %s" % value.quantize(TWOPLACES))

        sessionCookieTimeout = getattr(settings, 'GOOGLE_ANALYTICS_SESSION_COOKIE_TIMEOUT_SECONDS', False)
        if sessionCookieTimeout is not False:
            value = decimal.Decimal(sessionCookieTimeout)
            if value < 0:
                raise AnalyticalException("'GOOGLE_ANALYTICS_SESSION_COOKIE_TIMEOUT_SECONDS' must be >= 0")
            argstrings.append("'cookieExpires' : %s" % value.quantize(ZEROPLACES))

        siteSpeedSampleRate = getattr(settings, 'GOOGLE_ANALYTICS_SITE_SPEED_SAMPLE_RATE', False)
        if siteSpeedSampleRate is not False:
            value = decimal.Decimal(siteSpeedSampleRate)
            if not 0 <= value <= 100:
                raise AnalyticalException(
                    "'GOOGLE_ANALYTICS_SITE_SPEED_SAMPLE_RATE' must be >= 0 and <= 100")
            argstrings.append("'siteSpeedSampleRate' : %s" % value.quantize(TWOPLACES))

        argstring = ','.join(argstrings)
        additional_args = ""
        if argstring:
            additional_args = ", " + "{" + argstring + "}"
        command = CREATE_CODE % {
            'property_id': self.property_id,
            'additional_args': additional_args,
        }
        return command

    def _get_custom_var_commands(self, context):
        values = (
            context.get('google_analytics_var%s' % i) for i in range(1, 10)
        )
        params = [(i, v) for i, v in enumerate(values, 1) if v is not None]
        commands = []
        for index, var in params:
            name = var[0]
            value = var[1]
            commands.append(CUSTOM_VAR_CODE % {
                'name': name,
                'value': value,
            })
        return commands

    def _get_other_commands(self, context):
        commands = []
        if getattr(settings, 'GOOGLE_ANALYTICS_ANONYMIZE_IP', False):
            commands.append(ANONYMIZE_IP_CODE)

        return commands


def contribute_to_analytical(add_node):
    GoogleAnalyticsNode()  # ensure properly configured
    add_node('head_bottom', GoogleAnalyticsNode)
