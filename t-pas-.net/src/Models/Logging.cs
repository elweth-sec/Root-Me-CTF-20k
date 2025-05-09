using System.Diagnostics;

namespace CheaterReport.Models
{
    public class Logging
    {
        public Logging(string logged_string)
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "/bin/bash",
                Arguments = $"-c \"echo Logging: {logged_string}\"",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            });
        }
    }
}
